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

    # ---------------- EXPERIMENT ---------------- #

    def save_experiment(self, data):
        self.cursor.execute("""
            INSERT INTO experiments (name)
            VALUES (%s)
            RETURNING id
        """, (data.get("name", "Experiment"),))

        experiment_id = self.cursor.fetchone()[0]
        self.conn.commit()

        return experiment_id

    def get_experiments(self):
        self.cursor.execute("""
            SELECT id, name, created_at
            FROM experiments
            ORDER BY created_at DESC
        """)
        return self.cursor.fetchall()

    # ---------------- EPOCHS ---------------- #

    def save_epochs(self, experiment_id, data):

        t = data["t"]
        dx = data["dx"]
        dy = data["dy"]
        dz = data["dz"]

        # пока без RTN и clk (добавим завтра)
        records = []

        for i in range(len(t)):
            records.append((
                experiment_id,
                float(t[i]),
                "R12",  # временно
                float(dx[i]),
                float(dy[i]),
                float(dz[i]),
                None, None, None, None
            ))

        self.cursor.executemany("""
            INSERT INTO epochs (
                experiment_id, epoch_time, satellite,
                dx, dy, dz, dr, dt, dn, clock_error
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, records)

        self.conn.commit()

    def get_epochs(self, experiment_id):
        self.cursor.execute("""
            SELECT epoch_time, dx, dy, dz, dr, dt, dn, clock_error
            FROM epochs
            WHERE experiment_id = %s
            ORDER BY epoch_time
        """, (experiment_id,))

        rows = self.cursor.fetchall()

        # превращаем в dict (удобно для графиков)
        data = {
            "t": [],
            "dx": [],
            "dy": [],
            "dz": [],
            "dr": [],
            "dt": [],
            "dn": [],
            "clk": []
        }

        for row in rows:
            data["t"].append(row[0])
            data["dx"].append(row[1])
            data["dy"].append(row[2])
            data["dz"].append(row[3])
            data["dr"].append(row[4])
            data["dt"].append(row[5])
            data["dn"].append(row[6])
            data["clk"].append(row[7])

        return data

    # ---------------- STATISTICS ---------------- #

    def save_statistics(self, experiment_id, stats):

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
            stats.get("rms_x"),
            stats.get("rms_y"),
            stats.get("rms_z"),
            stats.get("rms_3d"),
            stats.get("rms_r"),
            stats.get("rms_t"),
            stats.get("rms_n"),
            stats.get("mean"),
            stats.get("max"),
            stats.get("clock_rms")
        ))

        self.conn.commit()

    def get_statistics(self, experiment_id):

        self.cursor.execute("""
            SELECT
                rms_x, rms_y, rms_z, rms_3d,
                rms_r, rms_t, rms_n,
                mean_error, max_error,
                clock_rms
            FROM statistics
            WHERE experiment_id = %s
        """, (experiment_id,))

        row = self.cursor.fetchone()

        if not row:
            return {}

        return {
            "rms_x": row[0],
            "rms_y": row[1],
            "rms_z": row[2],
            "rms_3d": row[3],
            "rms_r": row[4],
            "rms_t": row[5],
            "rms_n": row[6],
            "mean": row[7],
            "max": row[8],
            "clock_rms": row[9]
        }