"""
Pre-migration: rename accepted_signature_name → accepted_signature
in any ir.ui.view arches that still reference the old field name,
so view validation during the upgrade does not fail.
"""


def migrate(cr, version):
    # Patch stale view arches in the database
    cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = replace(arch_db::text, 'accepted_signature_name', 'accepted_signature')
        WHERE arch_db::text LIKE '%accepted_signature_name%'
    """)

    # Rename the database column if it still exists
    cr.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name = 'sale_order'
                AND   column_name = 'accepted_signature_name'
            ) THEN
                ALTER TABLE sale_order
                RENAME COLUMN accepted_signature_name TO accepted_signature;
            END IF;
        END
        $$;
    """)
