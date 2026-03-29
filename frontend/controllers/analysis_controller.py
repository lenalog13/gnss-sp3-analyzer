import numpy as np
from database.db_manager import DBManager

class AnalysisController:

    def __init__(self, db_manager, analysis_service):
        self.db = db_manager
        self.service = analysis_service

    # ---------------- RUN ANALYSIS ---------------- #

    def run_analysis(self, calc_path, ref_path, clk_path, satellite):
        """
        Основной метод запуска анализа
        """

        # 1. Валидация
        if not calc_path or not ref_path:
            raise ValueError("SP3 files are required")

        # 2. Запуск анализа (пока без парсера)
        result = self.service.run_analysis(
            calc_path,
            ref_path,
            clk_path,
            satellite
        )

        # 3. Сохранение в БД
        experiment_id = self.db.save_experiment({
            "calc_file": calc_path,
            "ref_file": ref_path,
            "clk_file": clk_path,
            "satellite": satellite
        })

        # 4. Сохранение эпох
        self.db.save_epochs(experiment_id, result)

        # 5. Сохранение статистики
        stats = self.calculate_statistics(result)
        self.db.save_statistics(experiment_id, stats)

        # 6. Возвращаем всё в GUI
        return {
            "experiment_id": experiment_id,
            "data": result,
            "stats": stats
        }

    # ---------------- LOAD FROM DB ---------------- #

    def load_experiment(self, experiment_id):
        """
        Загрузка эксперимента из БД
        """

        data = self.db.get_epochs(experiment_id)
        stats = self.db.get_statistics(experiment_id)

        return {
            "data": data,
            "stats": stats
        }

    # ---------------- HISTORY ---------------- #

    def get_history(self):
        """
        Получить список экспериментов
        """
        return self.db.get_experiments()

    # ---------------- STATS ---------------- #

    def calculate_statistics(self, data):

        dx = data["dx"]
        dy = data["dy"]
        dz = data["dz"]

        def rms(x):
            return float(np.sqrt(np.mean(x**2)))

        stats = {
            "rms_x": rms(dx),
            "rms_y": rms(dy),
            "rms_z": rms(dz),
            "rms_3d": rms(np.sqrt(dx**2 + dy**2 + dz**2)),
            "mean": float(np.mean(dx)),
            "max": float(np.max(np.abs(dx)))
        }

        return stats