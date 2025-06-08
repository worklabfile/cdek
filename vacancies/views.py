import requests
from django.shortcuts import render
from .forms import JobSearchForm
from .models import Vacancy
from .utils import *
import time

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
    if request.method == 'POST':
        form = JobSearchForm(request.POST)
        if form.is_valid():
            profession = form.cleaned_data['profession']
            salary = form.cleaned_data['salary']
            region = form.cleaned_data['region']

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
                response.raise_for_status()  # Проверка на ошибки HTTP
                data = response.json()
                vacancies_data = data.get('items', [])
                
                # Сохраняем вакансии в базу данных
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

                # Экспортируем в CSV
                try:
                    export_to_csv()
                except Exception as e:
                    print(f"Ошибка при экспорте в CSV: {e}")

                # Форматируем данные для отображения
                formatted_vacancies = []
                for vacancy in saved_vacancies:
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

                return render(request, 'vacancies/job_search.html', {
                    'form': form,
                    'vacancies': formatted_vacancies,
                    'search_performed': True
                })

            except requests.RequestException as e:
                error_message = f"Ошибка при запросе к API: {str(e)}"
                return render(request, 'vacancies/job_search.html', {
                    'form': form,
                    'error': error_message
                })
    else:
        form = JobSearchForm()

    return render(request, 'vacancies/job_search.html', {'form': form})
