from django.db import models

class Vacancy(models.Model):
    query = models.CharField(max_length=255, verbose_name="Исходный запрос", default="Нет данных")
    title = models.CharField(max_length=255, verbose_name="Название вакансии")
    salary_from = models.IntegerField(null=True, blank=True, verbose_name="Зарплата от")
    salary_to = models.IntegerField(null=True, blank=True, verbose_name="Зарплата до")
    currency = models.CharField(max_length=10, null=True, blank=True, verbose_name="Валюта")
    employer = models.CharField(max_length=255, null=True, blank=True, verbose_name="Работодатель")
    url = models.URLField(verbose_name="Ссылка на вакансию")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    benefits = models.TextField(null=True, blank=True, verbose_name="Неденежные бенефиты")
    is_internal = models.BooleanField(default=False, verbose_name="Внутренняя вакансия")
    user_salary = models.IntegerField(null=True, blank=True)
    
    @property
    def salary(self):
        if self.salary_from and self.salary_to:
            return (self.salary_from + self.salary_to) // 2
        return self.salary_from or self.salary_to or 0

    def __str__(self):
        return self.title
