import psycopg2
from contextlib import contextmanager

class DBManager:

    def __init__(self):
        self.conn = psycopg2.connect(
            dbname="gnss_db",
            user="postgres",
            password="8160",
            host="localhost",
            port="5432"
        )
    
    @contextmanager
    def get_cursor(self):
        """Контекстный менеджер для курсора"""
        cursor = self.conn.cursor()
        try:
            yield cursor
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise
        finally:
            cursor.close()
    
    # ---------------- EXPERIMENT ---------------- #

    def save_experiment(self, data):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO experiments (name)
                VALUES (%s)
                ON CONFLICT (name) DO UPDATE SET name = EXCLUDED.name
                RETURNING id
            """, (data.get("name", "Experiment"),))

            return cursor.fetchone()[0]

    def get_experiments(self):
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT id, name, created_at
                FROM experiments
                ORDER BY created_at DESC
            """)
            return cursor.fetchall()
        
    def get_experiment_by_name(self, name):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT id FROM experiments WHERE name = %s", (name,))
            result = cursor.fetchone()
            return result[0] if result else None
        
    
    # ---------------- EPOCHS ---------------- #

    def save_epochs(self, experiment_id, epochs):
        records = []
        for e in epochs:
            records.append((
                experiment_id,
                float(e["t"]),
                e["sat"],
                float(e["dx"]),
                float(e["dy"]),
                float(e["dz"]),
                float(e["dr"]) if e["dr"] is not None else None,
                float(e["dt"]) if e["dt"] is not None else None,
                float(e["dn"]) if e["dn"] is not None else None,
                float(e["clk"]) if e["clk"] is not None else None
))
        
        with self.get_cursor() as cursor:
            cursor.executemany("""
                INSERT INTO epochs (
                    experiment_id, epoch_time, satellite,
                    dx, dy, dz, dr, dt, dn, clock_error
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (experiment_id, epoch_time, satellite) DO NOTHING
            """, records)
            # commit автоматический

    def get_epochs(self, experiment_id, satellite=None):
        with self.get_cursor() as cursor:
            if satellite:
                cursor.execute("""
                    SELECT epoch_time, dx, dy, dz, dr, dt, dn, clock_error
                    FROM epochs
                    WHERE experiment_id = %s AND satellite = %s
                    ORDER BY epoch_time
                """, (experiment_id, satellite))
            else:
                cursor.execute("""
                    SELECT epoch_time, dx, dy, dz, dr, dt, dn, clock_error
                    FROM epochs
                    WHERE experiment_id = %s
                    ORDER BY epoch_time
                """, (experiment_id,))
            
            rows = cursor.fetchall()
        
        # Формируем словарь вне контекста
        data = {
            "t": [], "dx": [], "dy": [], "dz": [],
            "dr": [], "dt": [], "dn": [], "clk": []
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
    
    def delete_epochs(self, experiment_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM epochs WHERE experiment_id = %s
            """, (experiment_id,))
    
    # ---------------- SATELLITE ---------------- #

    def get_satellites(self, experiment_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT satellite
                FROM epochs
                WHERE experiment_id = %s
                ORDER BY satellite
            """, (experiment_id,))
            return [row[0] for row in cursor.fetchall()]
    
    # ---------------- STATISTICS ---------------- #

    def save_statistics(self, experiment_id, stats):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO statistics (
                    experiment_id, rms_x, rms_y, rms_z, rms_3d,
                    rms_r, rms_t, rms_n, mean_error, max_error, clock_rms
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
            # commit автоматический

    def get_statistics(self, experiment_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT
                    rms_x, rms_y, rms_z, rms_3d,
                    rms_r, rms_t, rms_n,
                    mean_error, max_error, clock_rms
                FROM statistics
                WHERE experiment_id = %s
            """, (experiment_id,))
            
            row = cursor.fetchone()
        
        if not row:
            return {}
        
        return {
            "rms_x": row[0], "rms_y": row[1], "rms_z": row[2],
            "rms_3d": row[3], "rms_r": row[4], "rms_t": row[5],
            "rms_n": row[6], "mean": row[7], "max": row[8],
            "clock_rms": row[9]
        }
    
    def delete_statistics(self, experiment_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM statistics
                WHERE experiment_id = %s
            """, (experiment_id,))

    # ---------------- FILES ---------------- #

    def save_files(self, experiment_id, calc_path, ref_path, clk_path):
        files = [
            ("calc", calc_path),
            ("ref", ref_path)
        ]

        if clk_path:
            files.append(("clk", clk_path))

        with self.get_cursor() as cursor:
            cursor.executemany("""
                INSERT INTO files (experiment_id, type, path)
                VALUES (%s, %s, %s)
            """, [
                (experiment_id, ftype, path)
                for ftype, path in files
            ])

    def delete_files(self, experiment_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                DELETE FROM files WHERE experiment_id = %s
            """, (experiment_id,))


    def close(self):
        """Закрыть соединение"""
        if self.conn:
            self.conn.close()
    
    def __enter__(self):
        """Для использования с with: with DBManager() as db:"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Автоматическое закрытие соединения"""
        self.close()