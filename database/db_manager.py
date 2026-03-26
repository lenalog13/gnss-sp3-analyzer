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

        def insert_statistics(self, experiment_id, stats):

            self.cursor.execute("""
                INSERT INTO statistics (
                    experiment_id,
                    rms_x, rms_y, rms_z, rms_3d,
                    rms_r, rms_t, rms_n,
                    mean_error, max_error,
                    clock_rms
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                experiment_id,
                stats["rms_x"], stats["rms_y"], stats["rms_z"], stats["rms_3d"],
                stats["rms_r"], stats["rms_t"], stats["rms_n"],
                stats["mean"], stats["max"],
                stats["clock_rms"]
            ))

            self.conn.commit()