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

def convert_to_rubles(salary, currency):
    if not salary or not currency:
        return None
    
    # Курсы валют (можно вынести в конфигурацию или получать через API)
    exchange_rates = {
        'RUR': 1,
        'RUB': 1,
        'USD': 90,  # Примерный курс
        'EUR': 100,  # Примерный курс
        'KZT': 0.2,  # Примерный курс
        'BYR': 30,   # Примерный курс
        'UAH': 2.5,  # Примерный курс
        'UZS': 0.007 # Примерный курс
    }
    
    rate = exchange_rates.get(currency.upper(), 1)
    return int(salary * rate)

def job_search_view(request):
    vacancies = []
    search_performed = False
    error = None
    user_salary = None
    
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
                            url=vacancy['alternate_url'],
                            user_salary=user_salary  # Сохраняем зарплату пользователя
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
        'user_salary': user_salary,
    }
    return render(request, 'vacancies/job_search.html', context)

def statistics_view(request):
    # Получаем последнюю введенную вакансию для определения последнего запроса
    last_vacancy = Vacancy.objects.order_by('-id').first()
    last_query = last_vacancy.query if last_vacancy else None

    # Если есть последний запрос, фильтруем вакансии по нему
    if last_query:
        vacancies = Vacancy.objects.filter(query=last_query)
    else:
        vacancies = Vacancy.objects.none() # Если запросов нет, то и вакансий нет
    
    # Общее количество вакансий
    total_vacancies = vacancies.count()
    
    # Конвертируем все зарплаты в рубли
    salaries_in_rubles = []
    formatted_vacancies = []
    for vacancy in vacancies:
        if vacancy.salary_from and vacancy.currency:
            salary_in_rubles = convert_to_rubles(vacancy.salary_from, vacancy.currency)
            if salary_in_rubles:
                salaries_in_rubles.append(salary_in_rubles)

        formatted_vacancies.append({
            'title': vacancy.title,
            'salary': format_salary({
                'from': vacancy.salary_from,
                'to': vacancy.salary_to,
                'currency': vacancy.currency
            }),
            'employer': vacancy.employer,
            'url': vacancy.url
        })
    
    # Статистика по зарплатам
    median_salary = int(statistics.median(salaries_in_rubles)) if salaries_in_rubles else 0
    min_salary = min(salaries_in_rubles) if salaries_in_rubles else 0
    max_salary = max(salaries_in_rubles) if salaries_in_rubles else 0
    
    # Создаем диапазоны зарплат для гистограммы
    salary_ranges = [
        '0-50k', '50k-100k', '100k-150k', '150k-200k',
        '200k-250k', '250k-300k', '300k-350k', '350k-400k', '400k+'
    ]
    
    # Подсчитываем количество вакансий в каждом диапазоне
    salary_counts = [0] * len(salary_ranges)
    for salary in salaries_in_rubles:
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
    
    # Получаем последнюю введенную зарплату (уже из последней вакансии)
    user_salary = last_vacancy.user_salary if last_vacancy else None
    
    context = {
        'total_vacancies': total_vacancies,
        'median_salary': median_salary,
        'min_salary': min_salary,
        'max_salary': max_salary,
        'salary_ranges': salary_ranges,
        'salary_counts': salary_counts,
        'user_salary': user_salary,
        'vacancies': formatted_vacancies,
    }
    
    return render(request, 'vacancies/statistics.html', context)
