CREATE OR REPLACE PROCEDURE public.schedule_delivery(
    IN p_route_id BIGINT,
    IN p_truck_id BIGINT,
    IN p_driver_id BIGINT,
    IN p_assistant_id BIGINT,
    IN p_start_timestamp TIMESTAMPTZ,
    IN p_end_timestamp TIMESTAMPTZ,
    IN p_order_item_ids BIGINT[],
    IN p_created_by UUID DEFAULT NULL,
    INOUT p_schedule_id BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
SET search_path = public, pg_temp
AS $$
DECLARE
    v_route public.routes%ROWTYPE;
    v_truck public.trucks%ROWTYPE;
    v_driver public.employees%ROWTYPE;
    v_assistant public.employees%ROWTYPE;
    v_item RECORD;
    v_item_count INTEGER := 0;
    v_load NUMERIC := 0;
    v_duration_hours NUMERIC;
    v_week_local TIMESTAMP;
    v_week_start TIMESTAMPTZ;
    v_week_end TIMESTAMPTZ;
    v_new_week_hours NUMERIC;
    v_driver_hours NUMERIC;
    v_assistant_hours NUMERIC;
BEGIN
    p_schedule_id := NULL;

    IF p_route_id IS NULL OR p_truck_id IS NULL
       OR p_driver_id IS NULL OR p_assistant_id IS NULL THEN
        RAISE EXCEPTION 'Route, truck, driver and assistant are required';
    END IF;

    IF p_driver_id = p_assistant_id THEN
        RAISE EXCEPTION 'Driver and assistant must be different employees';
    END IF;

    IF p_start_timestamp IS NULL OR p_end_timestamp IS NULL
       OR NOT isfinite(p_start_timestamp) OR NOT isfinite(p_end_timestamp)
       OR p_end_timestamp <= p_start_timestamp THEN
        RAISE EXCEPTION 'Delivery requires finite timestamps with end after start';
    END IF;

    IF p_start_timestamp < CURRENT_TIMESTAMP THEN
        RAISE EXCEPTION 'Delivery cannot be scheduled in the past';
    END IF;

    IF COALESCE(cardinality(p_order_item_ids), 0) = 0 THEN
        RAISE EXCEPTION 'At least one order item is required';
    END IF;

    IF array_ndims(p_order_item_ids) <> 1
       OR (SELECT COUNT(DISTINCT item_id)
           FROM unnest(p_order_item_ids) AS requested(item_id))
          <> cardinality(p_order_item_ids) THEN
        RAISE EXCEPTION 'Order item IDs must be a one-dimensional array without NULLs or duplicates';
    END IF;

    IF current_setting('transaction_isolation') = 'repeatable read' THEN
        RAISE EXCEPTION 'Scheduling requires READ COMMITTED or SERIALIZABLE isolation';
    END IF;

    LOCK TABLE public.truck_schedules, public.truck_item_deliveries
        IN SHARE ROW EXCLUSIVE MODE;

    SELECT r.* INTO v_route
    FROM public.routes AS r WHERE r.id = p_route_id FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Route % does not exist', p_route_id;
    END IF;

    v_duration_hours := EXTRACT(EPOCH FROM
        (p_end_timestamp - p_start_timestamp)) / 3600.0;
    IF v_duration_hours > v_route.max_delivery_time_hrs THEN
        RAISE EXCEPTION 'Delivery duration % hours exceeds route % maximum of % hours',
            v_duration_hours, p_route_id, v_route.max_delivery_time_hrs;
    END IF;

    SELECT t.* INTO v_truck
    FROM public.trucks AS t WHERE t.id = p_truck_id FOR SHARE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Truck % does not exist', p_truck_id;
    END IF;

    IF v_truck.vehicle_status <> 'Active'
       OR v_truck.store_id <> v_route.store_id
       OR (v_truck.route_id IS NOT NULL AND v_truck.route_id <> p_route_id) THEN
        RAISE EXCEPTION 'Truck % must be active and assigned to the route store and compatible route',
            p_truck_id;
    END IF;

    PERFORM e.id FROM public.employees AS e
    WHERE e.id IN (p_driver_id, p_assistant_id)
    ORDER BY e.id FOR SHARE;

    SELECT e.* INTO v_driver
    FROM public.employees AS e WHERE e.id = p_driver_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Driver % does not exist', p_driver_id;
    END IF;

    SELECT e.* INTO v_assistant
    FROM public.employees AS e WHERE e.id = p_assistant_id;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Assistant % does not exist', p_assistant_id;
    END IF;

    IF v_driver.employee_role <> 'DRIVER'
       OR v_driver.employee_status <> 'Available'
       OR v_driver.store_id <> v_route.store_id THEN
        RAISE EXCEPTION 'Employee % must be an available driver at the route store', p_driver_id;
    END IF;

    IF v_assistant.employee_role <> 'ASSISTANT'
       OR v_assistant.employee_status <> 'Available'
       OR v_assistant.store_id <> v_route.store_id THEN
        RAISE EXCEPTION 'Employee % must be an available assistant at the route store', p_assistant_id;
    END IF;

    IF EXISTS (
        SELECT 1 FROM public.truck_schedules AS s
        WHERE s.start_timestamp < p_end_timestamp
          AND s.end_timestamp > p_start_timestamp
          AND (s.truck_id = p_truck_id
               OR s.driver_id IN (p_driver_id, p_assistant_id)
               OR s.assistant_id IN (p_driver_id, p_assistant_id))
    ) THEN
        RAISE EXCEPTION 'Truck, driver or assistant has an overlapping delivery';
    END IF;

    IF EXISTS (
        SELECT 1 FROM public.truck_schedules AS s
        WHERE (s.driver_id = p_driver_id OR s.assistant_id = p_driver_id)
          AND (s.end_timestamp = p_start_timestamp
               OR s.start_timestamp = p_end_timestamp)
    ) THEN
        RAISE EXCEPTION 'Driver % cannot work consecutive deliveries without a rest interval',
            p_driver_id;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM public.truck_schedules AS a
        JOIN public.truck_schedules AS b ON a.id <> b.id
        WHERE (a.assistant_id = p_assistant_id OR a.driver_id = p_assistant_id)
          AND (b.assistant_id = p_assistant_id OR b.driver_id = p_assistant_id)
          AND (
              (a.end_timestamp = p_start_timestamp AND b.end_timestamp = a.start_timestamp)
              OR (a.start_timestamp = p_end_timestamp AND b.start_timestamp = a.end_timestamp)
              OR (a.end_timestamp = p_start_timestamp AND b.start_timestamp = p_end_timestamp)
          )
    ) THEN
        RAISE EXCEPTION 'Assistant % cannot work more than two consecutive deliveries',
            p_assistant_id;
    END IF;

    v_week_local := date_trunc('week', p_start_timestamp AT TIME ZONE 'Asia/Colombo');
    WHILE v_week_local < (p_end_timestamp AT TIME ZONE 'Asia/Colombo') LOOP
        v_week_start := v_week_local AT TIME ZONE 'Asia/Colombo';
        v_week_end := (v_week_local + INTERVAL '1 week') AT TIME ZONE 'Asia/Colombo';
        v_new_week_hours := EXTRACT(EPOCH FROM
            (LEAST(p_end_timestamp, v_week_end)
             - GREATEST(p_start_timestamp, v_week_start))) / 3600.0;

        SELECT
            COALESCE(SUM(EXTRACT(EPOCH FROM
                (LEAST(s.end_timestamp, v_week_end)
                 - GREATEST(s.start_timestamp, v_week_start))) / 3600.0)
                FILTER (WHERE s.driver_id = p_driver_id OR s.assistant_id = p_driver_id), 0),
            COALESCE(SUM(EXTRACT(EPOCH FROM
                (LEAST(s.end_timestamp, v_week_end)
                 - GREATEST(s.start_timestamp, v_week_start))) / 3600.0)
                FILTER (WHERE s.assistant_id = p_assistant_id OR s.driver_id = p_assistant_id), 0)
        INTO v_driver_hours, v_assistant_hours
        FROM public.truck_schedules AS s
        WHERE s.start_timestamp < v_week_end AND s.end_timestamp > v_week_start
          AND (s.driver_id IN (p_driver_id, p_assistant_id)
               OR s.assistant_id IN (p_driver_id, p_assistant_id));

        IF v_driver_hours + v_new_week_hours > 40 THEN
            RAISE EXCEPTION 'Driver % exceeds 40 hours in the week beginning %',
                p_driver_id, v_week_local::DATE;
        END IF;
        IF v_assistant_hours + v_new_week_hours > 60 THEN
            RAISE EXCEPTION 'Assistant % exceeds 60 hours in the week beginning %',
                p_assistant_id, v_week_local::DATE;
        END IF;

        v_week_local := v_week_local + INTERVAL '1 week';
    END LOOP;

    FOR v_item IN
        SELECT oi.id, oi.quantity, oi.item_lifecycle_status,
               o.route_id, o.order_date, p.space_consumption_unit
        FROM public.order_items AS oi
        JOIN public.orders AS o ON o.id = oi.order_id
        JOIN public.products AS p ON p.id = oi.product_id
        WHERE oi.id = ANY(p_order_item_ids)
        ORDER BY oi.id
        FOR UPDATE OF oi FOR SHARE OF o, p
    LOOP
        v_item_count := v_item_count + 1;
        IF v_item.route_id <> p_route_id THEN
            RAISE EXCEPTION 'Order item % belongs to a different delivery route', v_item.id;
        END IF;
        IF v_item.order_date + INTERVAL '7 days' > p_start_timestamp THEN
            RAISE EXCEPTION 'Order item % requires at least seven days between ordering and delivery',
                v_item.id;
        END IF;
        IF v_item.item_lifecycle_status <> 'STORE_RECEIVED' THEN
            RAISE EXCEPTION 'Order item % must be STORE_RECEIVED before scheduling delivery', v_item.id;
        END IF;
        IF EXISTS (
            SELECT 1 FROM public.truck_item_deliveries AS d
            WHERE d.order_item_id = v_item.id
        ) THEN
            RAISE EXCEPTION 'Order item % already has a truck delivery assignment', v_item.id;
        END IF;
        PERFORM a.id
        FROM public.train_allocations AS a
        JOIN public.train_schedules AS t ON t.id = a.train_id
        WHERE a.order_item_id = v_item.id
          AND t.destination_store_id = v_route.store_id
          AND t.departure_timestamp <= p_start_timestamp
        FOR SHARE OF a, t;
        IF NOT FOUND THEN
            RAISE EXCEPTION 'Order item % has no compatible train allocation to the route store', v_item.id;
        END IF;
        v_load := v_load + v_item.quantity * v_item.space_consumption_unit;
    END LOOP;

    IF v_item_count <> cardinality(p_order_item_ids) THEN
        RAISE EXCEPTION 'One or more requested order items do not exist';
    END IF;
    IF v_load > v_truck.capacity THEN
        RAISE EXCEPTION 'Delivery load % exceeds truck % capacity %',
            v_load, p_truck_id, v_truck.capacity;
    END IF;

    INSERT INTO public.truck_schedules (
        truck_id, route_id, driver_id, assistant_id,
        start_timestamp, end_timestamp, created_by, updated_by
    ) VALUES (
        p_truck_id, p_route_id, p_driver_id, p_assistant_id,
        p_start_timestamp, p_end_timestamp, p_created_by, p_created_by
    ) RETURNING id INTO p_schedule_id;

    INSERT INTO public.truck_item_deliveries (truck_schedule_id, order_item_id)
    SELECT p_schedule_id, item_id
    FROM unnest(p_order_item_ids) AS requested(item_id);

    UPDATE public.order_items
    SET item_lifecycle_status = 'OUT_FOR_DELIVERY'
    WHERE id = ANY(p_order_item_ids);
END;
$$;