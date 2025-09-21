# Traceability

| Требование | Компонент/эндпоинт         | Тест/Проверка               |
|------------|----------------------------|-----------------------------|
| FR-1       | /api/auth/login            | test_login_ok_and_bad       |
| FR-2       | /api/projects              | test_projects_role_access   |
| FR-3       | /api/defects (POST/PATCH)  | test_defect_create_and_filters |
| FR-4       | /api/defects (GET)         | test_defect_create_and_filters |
| FR-5       | /api/upload + UI           | ручной smoke                |
| FR-6       | /api/reports/summary       | test_report_summary         |
| NFR-2      | logs/app.log               | визуально                   |
| NFR-4      | pytest + CI                | workflow                    |
