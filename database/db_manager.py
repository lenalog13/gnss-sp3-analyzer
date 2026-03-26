import psycopg2


class DBManager:

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="gnss_db",
            user="postgres",
            password="8160",
            host="localhost",
            port="5432"
)
        self.cursor = self.conn.cursor()

    def create_experiment(self, name):

        self.cursor.execute(
            "INSERT INTO experiments (name) VALUES (%s) RETURNING id",
            (name,)
        )

        experiment_id = self.cursor.fetchone()[0]
        self.conn.commit()

        return experiment_id

    def insert_epoch(self, experiment_id, epoch_data):

        self.cursor.execute("""
            INSERT INTO epochs (
                experiment_id, epoch_time, satellite,
                dx, dy, dz, dr, dt, dn, clock_error
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (
            experiment_id,
            epoch_data["t"],
            epoch_data["sat"],
            epoch_data["dx"],
            epoch_data["dy"],
            epoch_data["dz"],
            epoch_data["dr"],
            epoch_data["dt"],
            epoch_data["dn"],
            epoch_data["clk"]
        ))

        self.conn.commit()