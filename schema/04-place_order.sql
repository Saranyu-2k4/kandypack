-- ============================================================
-- KANDYPACK
-- Procedure: place_order
--
-- Purpose:
--   Place a new customer order with one or more products.
--
-- Business rules:
--   1. Customer must exist.
--   2. Route must exist.
--   3. Delivery must be at least 7 days in advance.
--   4. Order must contain at least one item.
--   5. Product IDs must exist.
--   6. Quantities must be greater than zero.
--   7. Product price is copied into order_items.unit_price
--      at the time the order is placed.
--   8. All newly created order items start with PLACED status.
--
--
-- ============================================================


CREATE OR REPLACE PROCEDURE place_order(
    IN  p_customer_id           BIGINT,
    IN  p_route_id              BIGINT,
    IN  p_delivery_address      TEXT,
    IN  p_contact_phone         VARCHAR(50),
    IN  p_preferred_slot        VARCHAR(100),
    IN  p_delivery_date         TIMESTAMPTZ,
    IN  p_items                  JSONB,
    IN  p_created_by             UUID DEFAULT NULL,
    INOUT p_order_id             BIGINT DEFAULT NULL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_customer_exists       BOOLEAN;
    v_route_exists          BOOLEAN;
    v_product_exists        BOOLEAN;
    v_product_id            BIGINT;
    v_quantity              INTEGER;
    v_unit_price            NUMERIC(12, 2);
    v_item                  JSONB;
    v_item_count            INTEGER;
    v_order_id              BIGINT;
    v_customer_route_id     BIGINT;
    v_route_store_id        BIGINT;

BEGIN

    IF p_customer_id IS NULL THEN
        RAISE EXCEPTION
            'Customer ID cannot be NULL';
    END IF;

    IF p_route_id IS NULL THEN
        RAISE EXCEPTION
            'Route ID cannot be NULL';
    END IF;

    IF p_delivery_address IS NULL
       OR trim(p_delivery_address) = '' THEN

        RAISE EXCEPTION
            'Delivery address cannot be empty';
    END IF;

    IF p_contact_phone IS NULL
       OR trim(p_contact_phone) = '' THEN
        RAISE EXCEPTION
            'Contact phone cannot be empty';
    END IF;

    IF p_delivery_date IS NULL THEN
        RAISE EXCEPTION
            'Delivery date cannot be NULL';
    END IF;

    IF p_items IS NULL
       OR jsonb_typeof(p_items) <> 'array' THEN
        RAISE EXCEPTION
            'Order items cannot be Null';
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM customers
        WHERE id = p_customer_id
    )
    INTO v_customer_exists;

    IF NOT v_customer_exists THEN
        RAISE EXCEPTION
            'Customer with ID % does not exist',
            p_customer_id;
    END IF;

    SELECT EXISTS (
        SELECT 1
        FROM routes
        WHERE id = p_route_id
    )
    INTO v_route_exists;

    IF NOT v_route_exists THEN
        RAISE EXCEPTION
            'Route with ID % does not exist',
            p_route_id;
    END IF;

    IF p_delivery_date < CURRENT_TIMESTAMP + INTERVAL '7 days' THEN
    RAISE EXCEPTION
        'Orders must be placed at least 7 days in advance';
    END IF;

    v_item_count := jsonb_array_length(p_items);

    IF v_item_count = 0 THEN
        RAISE EXCEPTION
            'Order must contain at least one item';
    END IF;

    FOR v_item IN
        SELECT value
        FROM jsonb_array_elements(p_items)
    LOOP

        IF NOT (v_item ? 'product_id') THEN
            RAISE EXCEPTION
                'Each order item must contain product_id';
        END IF;

        v_product_id :=
            (v_item ->> 'product_id')::BIGINT;

        IF NOT (v_item ? 'quantity') THEN
            RAISE EXCEPTION
                'Product % must contain quantity',
                v_product_id;
        END IF;

        v_quantity :=
            (v_item ->> 'quantity')::INTEGER;

        IF v_quantity IS NULL OR v_quantity <= 0 THEN
            RAISE EXCEPTION
                'Quantity for product % must be greater than zero',
                v_product_id;
        END IF;

        SELECT EXISTS (
            SELECT 1
            FROM products
            WHERE id = v_product_id
        )
        INTO v_product_exists;

        IF NOT v_product_exists THEN
            RAISE EXCEPTION
                'Product with ID % does not exist',
                v_product_id;
        END IF;

        SELECT unit_price
        INTO v_unit_price
        FROM products
        WHERE id = v_product_id;

        IF v_unit_price IS NULL THEN
            RAISE EXCEPTION
                'Product % has no valid unit price',
                v_product_id;
        END IF;
    END LOOP;
    

    IF EXISTS (
        SELECT product_id
        FROM jsonb_to_recordset(p_items)
        AS x(product_id BIGINT, quantity INTEGER)
        GROUP BY product_id
        HAVING COUNT(*) > 1
    ) THEN

        RAISE EXCEPTION
            'The same product cannot appear multiple times in one order';

    END IF;


    INSERT INTO orders (
        customer_id,
        route_id,
        delivery_address,
        contact_phone,
        order_date,
        prefered_delivery_slot,
        created_by,
        updated_by
    )
    VALUES (
        p_customer_id,
        p_route_id,
        p_delivery_address,
        p_contact_phone,
        CURRENT_TIMESTAMP,
        p_preferred_slot,
        p_created_by,
        p_created_by
    )
    RETURNING id
    INTO v_order_id;

    FOR v_item IN
        SELECT value
        FROM jsonb_array_elements(p_items)
    LOOP

        v_product_id :=
            (v_item ->> 'product_id')::BIGINT;
        v_quantity :=
            (v_item ->> 'quantity')::INTEGER;

        SELECT unit_price
        INTO v_unit_price
        FROM products
        WHERE id = v_product_id;

        INSERT INTO order_items (
            order_id,
            product_id,
            unit_price,
            quantity,
            item_lifecycle_status
        )
        VALUES (
            v_order_id,
            v_product_id,
            v_unit_price,
            v_quantity,
            'PLACED'
        );

    END LOOP;
    p_order_id := v_order_id;

    RAISE NOTICE
        'Order % successfully placed for customer %',
        v_order_id,
        p_customer_id;


EXCEPTION
    WHEN invalid_text_representation THEN
        RAISE EXCEPTION
            'Invalid product_id or quantity format in p_items JSON';

    WHEN numeric_value_out_of_range THEN
        RAISE EXCEPTION
            'Product ID or quantity is outside the allowed range';

    WHEN OTHERS THEN
        RAISE;

END;
$$;