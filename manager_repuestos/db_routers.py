class LegacyRouter:
    """
    Enruta modelos legacy según su tabla.
    """

    def db_for_read(self, model, **hints):

        # Tablas en base 'remota'
        if model._meta.db_table in [
            'material',
            'material2',
            'grupos',
            'equipos',
            'listamat',
        ]:
            return 'remota'


        # Tablas en rpg2
        if model._meta.db_table == 'seguimiento':
            return 'rpg2'

        # Tablas en clientes
        if model._meta.db_table == 'datos':
            return 'clientes'


        # Todo lo demás → default
        return None

    def db_for_write(self, model, **hints):

        # Nunca escribir en bases legacy
        if model._meta.db_table in [
            'seguimiento',
            'datos',
            'material',
            'material2',
            'grupos',
            'equipos',
            'listamat',
        ]:
            return None

        return None

    def allow_migrate(self, db, model):
        # Nunca migrar tablas legacy
        if model._meta.db_table in [
            'seguimiento',
            'datos',
            'material',
            'material2',
            'grupos',
            'equipos',
            'listamat',
        ]:
            return False

        return None
