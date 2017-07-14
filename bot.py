import telebot
from bs4 import BeautifulSoup
import requests
import datetime


access_token = ''
bot = telebot.TeleBot(access_token)


def get_page(group, week=''):
    if week:
        week = str(week) + '/'
    url = '{domain}/{group}/{week}raspisanie_zanyatiy_{group}.htm'.format(
        domain='http://www.ifmo.ru/ru/schedule/0',
        week=week,
        group=group)
    response = requests.get(url)
    web_page = response.text
    return web_page


weekdays_dict = {'monday':1,
                 'tuesday':2,
                 'wednesday':3,
                 'thursday':4,
                 'friday':5
                }

weekdays_dict2 = {1: 'Monday',
                  2: 'Tuesday',
                  3: 'Wednesday',
                  4: 'Thursday',
                  5: 'Friday'}



def get_schedule_for_day(web_page, weekday):
    soup = BeautifulSoup(web_page, "html5lib")

    # Получаем таблицу с расписанием на день недели
    if weekday in weekdays_dict:
        w_day = weekdays_dict[weekday]
    else:
        w_day = weekday
    schedule_table = soup.find("table", attrs={"id": (str(w_day)+"day")})

    # Время проведения занятий
    times_list = schedule_table.find_all("td", attrs={"class": "time"})
    times_list = [time.span.text for time in times_list]

    # Место проведения занятий
    locations_list = schedule_table.find_all("td", attrs={"class": "room"})
    locations_list = [room.span.text for room in locations_list]

    # Название дисциплин и имена преподавателей
    lessons_list = schedule_table.find_all("td", attrs={"class": "lesson"})
    lessons_list = [lesson.text.split('\n\n') for lesson in lessons_list]
    lessons_list = [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list]

    return times_list, locations_list, lessons_list


def get_shedule_for_week(web_page):
    soup = BeautifulSoup(web_page, "html5lib")

    for i in range(1,6):
        schedule_table = soup.find("table", attrs={"id": (str(i) + "day")})

        # Время проведения занятий
        times_list = schedule_table.find_all("td", attrs={"class": "time"})
        times_list = [time.span.text for time in times_list]

        # Место проведения занятий
        locations_list = schedule_table.find_all("td", attrs={"class": "room"})
        locations_list = [room.span.text for room in locations_list]

        # Название дисциплин и имена преподавателей
        lessons_list = schedule_table.find_all("td", attrs={"class": "lesson"})
        lessons_list = [lesson.text.split('\n\n') for lesson in lessons_list]
        lessons_list = [', '.join([info for info in lesson_info if info]) for lesson_info in lessons_list]

        yield times_list, locations_list, lessons_list


@bot.message_handler(commands=['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
def get_day(message):
    week_num = 0
    mess_list = message.text.split()[:]
    try:
        if len(mess_list) == 3:
            week_day, group, week_num = mess_list
        # Если не указывают неделю
        else:
            week_day, group = mess_list
    except:
        pass
    web_page = get_page(group, week_num)
    weekday = week_day[1:]
    times_lst, locations_lst, lessons_lst = get_schedule_for_day(web_page, weekday)

    resp = ''
    for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
        resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)

    bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['tomorrow'])
def get_tomorrow(message):
    try:
        _, group = message.text.split()
    except:
        pass
    weekday = 0
    week_day = datetime.datetime.today().isoweekday()
    if str(week_day) in '1234':
        weekday = week_day + 1
    elif week_day == 7:
        weekday = 1
    week_diff = datetime.date.today().isocalendar()[1] - datetime.date(datetime.date.today().isocalendar()[0], 9, 1).isocalendar()[1]
    if weekday != 1:
        if week_diff % 2 == 0:
            week_num = 2
        else:
            week_num = 1
    else:
        if week_diff % 2 == 0:
            week_num = 1
        else:
            week_num = 2
    if weekday != 0:
        web_page = get_page(group, week_num)
        times_lst, locations_lst, lessons_lst = get_schedule_for_day(web_page, weekday)

        resp = ''
        for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
            resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)

        bot.send_message(message.chat.id, resp, parse_mode='HTML')
    else:
        bot.send_message(message.chat.id, 'Завтра нет пар', parse_mode='HTML')


@bot.message_handler(commands=['week_shedule'])
def get_week(message):
    try:
        _, group = message.text.split()
    except:
        pass
    week_diff = datetime.date.today().isocalendar()[1] - \
                datetime.date(datetime.date.today().isocalendar()[0], 9, 1).isocalendar()[1]
    if week_diff % 2 == 0:
        week_num = 2
    else:
        week_num = 1
    web_page = get_page(group, week_num)
    shedule_gen = get_shedule_for_week(web_page)

    for i in range(1, 6):
        times_lst, locations_lst, lessons_lst = next(shedule_gen)

        resp = '<b>' +'__' + str(weekdays_dict2[i]) + '__' +'</b>' + '\n\n'
        for time, location, lession in zip(times_lst, locations_lst, lessons_lst):
            resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)

        bot.send_message(message.chat.id, resp, parse_mode='HTML')


@bot.message_handler(commands=['next_class'])
def get_nextclass(message):
    try:
        _, group = message.text.split()
    except:
        pass
    weekday = datetime.date.today().isoweekday()
    week_diff = datetime.date.today().isocalendar()[1] - \
                datetime.date(datetime.date.today().isocalendar()[0], 9, 1).isocalendar()[1]
    if week_diff % 2 == 0:
        week_num = 2
    else:
        week_num = 1

    if str(weekday) in '12345':
        web_page = get_page(group, week_num)
        soup = BeautifulSoup(web_page, "html5lib")

        schedule_table = soup.find("table", attrs={"id": (str(weekday) + "day")})
        time_now = datetime.datetime.today().time()

        times_list = schedule_table.find_all("td", attrs={"class": "time"})
        times_list = [time.span.text for time in times_list]

        end_l = []
        beg_l = []
        for timee in times_list:
            beg, end = timee.split('-')
            end_l.append(end)
            beg_l.append(beg)
        h, m = end_l[-2].split(':')

        if time_now < datetime.time(hour = int(h), minute = int(m)):
            count_b = 0
            for beg in beg_l:
                h1, m1 = beg.split(':')
                if time_now < datetime.time(hour = int(h1), minute = int(m1)):
                    break
                count_b += 1
        else:
            if str(weekday) in '1234':
                weekday += 1
                count_b = 0
            else:
                weekday = 1
                if week_num == 1:
                    week_num =2
                else:
                    week_num = 1
    else:
        count_b = 0
        weekday = 1
        if week_num == 1:
            week_num = 2
        else:
            week_num = 1

    web_page = get_page(group, week_num)
    times_lst, locations_lst, lessons_lst = get_schedule_for_day(web_page, weekday)

    zip_v = list(zip(times_lst, locations_lst, lessons_lst))
    time, location, lession = zip_v[count_b]
    resp = '<b>' + '__' + str(weekdays_dict2[weekday]) + '__' + '</b>' + '\n\n'
    resp += '<b>{}</b>, {}, {}\n'.format(time, location, lession)
    bot.send_message(message.chat.id, resp, parse_mode='HTML')


if __name__ == '__main__':
    bot.polling(none_stop=True)
