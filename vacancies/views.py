import requests
from django.shortcuts import render
from .forms import JobSearchForm
from .models import Vacancy
from .utils import *
import time
import statistics
from collections import Counter
from django.db.models import Min, Max, Count
from django.db.models.functions import Cast
from django.db.models import IntegerField

def format_salary(salary):
    if not salary:
        return "Не указана"
    
    from_salary = salary.get('from')
    to_salary = salary.get('to')
    currency = salary.get('currency', 'RUR')
    
    if from_salary and to_salary:
        return f"{from_salary:,} - {to_salary:,} {currency}"
    elif from_salary:
        return f"от {from_salary:,} {currency}"
    elif to_salary:
        return f"до {to_salary:,} {currency}"
    return "Не указана"

def job_search_view(request):
    vacancies_qs = Vacancy.objects.filter(currency='RUR')
    # --- Статистика ---
    total_vacancies = vacancies_qs.count()
    salaries = [v.salary for v in vacancies_qs if v.salary]
    median_salary = int(statistics.median(salaries)) if salaries else 0
    min_salary = min(salaries) if salaries else 0
    max_salary = max(salaries) if salaries else 0
    salary_ranges = [
        '0-50k', '50k-100k', '100k-150k', '150k-200k',
        '200k-250k', '250k-300k', '300k-350k', '350k-400k', '400k+'
    ]
    salary_counts = [0] * len(salary_ranges)
    for salary in salaries:
        if salary <= 50000:
            salary_counts[0] += 1
        elif salary <= 100000:
            salary_counts[1] += 1
        elif salary <= 150000:
            salary_counts[2] += 1
        elif salary <= 200000:
            salary_counts[3] += 1
        elif salary <= 250000:
            salary_counts[4] += 1
        elif salary <= 300000:
            salary_counts[5] += 1
        elif salary <= 350000:
            salary_counts[6] += 1
        elif salary <= 400000:
            salary_counts[7] += 1
        else:
            salary_counts[8] += 1
    benefits = []
    for vacancy in vacancies_qs:
        if getattr(vacancy, 'benefits', None):
            benefits.extend(vacancy.benefits.split(','))
    benefits_counter = Counter([b.strip() for b in benefits if b.strip()])
    benefits_labels = list(benefits_counter.keys())
    benefits_data = list(benefits_counter.values())
    internal_salaries = [v.salary for v in vacancies_qs if getattr(v, 'is_internal', False) and v.salary]
    internal_median_salary = int(statistics.median(internal_salaries)) if internal_salaries else 0
    user_salary = None
    # --- Поиск ---
    vacancies = []
    search_performed = False
    error = None
    if request.method == 'POST':
        form = JobSearchForm(request.POST)
        if form.is_valid():
            profession = form.cleaned_data['profession']
            salary = form.cleaned_data['salary']
            region = form.cleaned_data['region']
            user_salary = salary if salary else None
            url = "https://api.hh.ru/vacancies" 
            params = {
                'text': profession,
                'area': get_region_id(region),
                'salary': salary,
                'only_with_salary': True if salary else False,
                'per_page': 10,
                'page': 0,
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                vacancies_data = data.get('items', [])
                saved_vacancies = []
                for vacancy in vacancies_data:
                    try:
                        saved_vacancy = Vacancy.objects.create(
                            query=profession,
                            title=vacancy['name'],
                            salary_from=vacancy.get('salary', {}).get('from'),
                            salary_to=vacancy.get('salary', {}).get('to'),
                            currency=vacancy.get('salary', {}).get('currency'),
                            employer=vacancy['employer']['name'],
                            url=vacancy['alternate_url']
                        )
                        saved_vacancies.append(saved_vacancy)
                    except Exception as e:
                        print(f"Ошибка при сохранении вакансии: {e}")
                        continue
                try:
                    export_to_csv()
                except Exception as e:
                    print(f"Ошибка при экспорте в CSV: {e}")
                for vacancy in saved_vacancies:
                    vacancies.append({
                        'title': vacancy.title,
                        'salary': format_salary({
                            'from': vacancy.salary_from,
                            'to': vacancy.salary_to,
                            'currency': vacancy.currency
                        }),
                        'employer': vacancy.employer,
                        'url': vacancy.url
                    })
                search_performed = True
            except requests.RequestException as e:
                error = f"Ошибка при запросе к API: {str(e)}"
    else:
        form = JobSearchForm()
    context = {
        'form': form,
        'vacancies': vacancies,
        'search_performed': search_performed,
        'error': error,
        'total_vacancies': total_vacancies,
        'median_salary': median_salary,
        'min_salary': min_salary,
        'max_salary': max_salary,
        'salary_ranges': salary_ranges,
        'salary_counts': salary_counts,
        'benefits_labels': benefits_labels,
        'benefits_data': benefits_data,
        'internal_median_salary': internal_median_salary,
        'user_salary': user_salary,
    }
    return render(request, 'vacancies/job_search.html', context)

def statistics_view(request):
    # Получаем все вакансии
    vacancies = Vacancy.objects.all()
    
    # Общее количество вакансий
    total_vacancies = vacancies.count()
    
    # Статистика по зарплатам
    salaries = list(vacancies.values_list('salary', flat=True))
    median_salary = int(statistics.median(salaries)) if salaries else 0
    min_salary = min(salaries) if salaries else 0
    max_salary = max(salaries) if salaries else 0
    
    # Создаем диапазоны зарплат для гистограммы
    salary_ranges = [
        '0-50k', '50k-100k', '100k-150k', '150k-200k',
        '200k-250k', '250k-300k', '300k-350k', '350k-400k', '400k+'
    ]
    
    # Подсчитываем количество вакансий в каждом диапазоне
    salary_counts = [0] * len(salary_ranges)
    for salary in salaries:
        if salary <= 50000:
            salary_counts[0] += 1
        elif salary <= 100000:
            salary_counts[1] += 1
        elif salary <= 150000:
            salary_counts[2] += 1
        elif salary <= 200000:
            salary_counts[3] += 1
        elif salary <= 250000:
            salary_counts[4] += 1
        elif salary <= 300000:
            salary_counts[5] += 1
        elif salary <= 350000:
            salary_counts[6] += 1
        elif salary <= 400000:
            salary_counts[7] += 1
        else:
            salary_counts[8] += 1
    
    # Анализ неденежных бенефитов
    benefits = []
    for vacancy in vacancies:
        if vacancy.benefits:
            benefits.extend(vacancy.benefits.split(','))
    
    benefits_counter = Counter(benefits)
    benefits_labels = list(benefits_counter.keys())
    benefits_data = list(benefits_counter.values())
    
    # Внутренняя медиана (предполагаем, что у нас есть поле is_internal)
    internal_salaries = list(vacancies.filter(is_internal=True).values_list('salary', flat=True))
    internal_median_salary = int(statistics.median(internal_salaries)) if internal_salaries else 0
    
    context = {
        'total_vacancies': total_vacancies,
        'median_salary': median_salary,
        'min_salary': min_salary,
        'max_salary': max_salary,
        'salary_ranges': salary_ranges,
        'salary_counts': salary_counts,
        'benefits_labels': benefits_labels,
        'benefits_data': benefits_data,
        'internal_median_salary': internal_median_salary,
    }
    
    return render(request, 'vacancies/statistics.html', context)
