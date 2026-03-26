import numpy as np
from database.db_manager import DBManager

class AnalysisController:

    def __init__(self):
        self.db = DBManager()

    def run_analysis(self, sp3_calc_path, sp3_ref_path, clk_path, satellite):

        import numpy as np

        # --- генерация (пока тестовая) ---
        t = np.linspace(0, 24, 200)

        dx = 0.1 * np.sin(t) + np.random.normal(0, 0.01, len(t))
        dy = 0.1 * np.cos(t) + np.random.normal(0, 0.01, len(t))
        dz = 0.05 * np.sin(2 * t) + np.random.normal(0, 0.01, len(t))

        dr = 0.05 * np.sin(t)
        dt = 0.08 * np.cos(t)
        dn = 0.03 * np.sin(2 * t)

        clk = np.random.normal(0, 5, len(t))

        #  1. создаём эксперимент
        exp_id = self.db.create_experiment("Test run")

        # 🔥 2. сохраняем эпохи
        for i in range(len(t)):
            self.db.insert_epoch(exp_id, {
                "t": float(t[i]),
                "sat": satellite,
                "dx": float(dx[i]),
                "dy": float(dy[i]),
                "dz": float(dz[i]),
                "dr": float(dr[i]),
                "dt": float(dt[i]),
                "dn": float(dn[i]),
                "clk": float(clk[i])
            })

        #  3. считаем статистику
        stats = self.compute_statistics(dx, dy, dz, dr, dt, dn, clk)

        #  4. сохраняем статистику
        self.db.insert_statistics(exp_id, stats)

        #  5. возвращаем в GUI
        return {
            "t": t,
            "dx": dx,
            "dy": dy,
            "dz": dz,
            "dr": dr,
            "dt": dt,
            "dn": dn,
            "clk": clk
        }
    
    def compute_statistics(self, dx, dy, dz, dr, dt, dn, clk):

        import numpy as np

        def rms(x):
            return np.sqrt(np.mean(x**2))

            return {
                "rms_x": rms(dx),
                "rms_y": rms(dy),
                "rms_z": rms(dz),
                "rms_3d": rms(np.sqrt(dx**2 + dy**2 + dz**2)),
                "rms_r": rms(dr),
                "rms_t": rms(dt),
                "rms_n": rms(dn),
                "mean": np.mean(dx),
                "max": np.max(np.abs(dx)),
                "clock_rms": rms(clk)
            }