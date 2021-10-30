import time
import re
import hashlib
import os
from .data import Question
from hoshino import aiorequests
from hoshino.service import Service, priv as Priv
from hoshino.typing import CommandSession
from peewee import fn
answers = {}
answersRegex = {}
sv = Service('QA', manage_priv=Priv.ADMIN, enable_on_default=False)
env = 'cq' # cq或者mirai

async def cqimage(a):
    if env == 'mirai':
        if r'[CQ:image,' in a:
            url = re.search(r'url=([\S]*)\]', a).group(1)
            a = f'[CQ:image,file=' + url + ']'
    return a

# recovery from database
for qu in Question.select().where(Question.allow_private == 0):
    answers[qu.quest] = {}

for qu in Question.select().where(Question.allow_private == 1):
    answersRegex[qu.quest] = {}


@sv.on_message('group')
async def setqa(bot, context):
    message = context['raw_message']
    if message.startswith('模糊问'):
        msg = message[3:].split('答', 1)
        if len(msg) == 1:
            return
        q, a = msg
        q = q.strip()
        if len(q) == 0:
            return
        if len(a) == 0:
            return
        if len(q) > 200:
            await bot.send(context, f'问得太长了~', at_sender=True)
            returnq
        #if len(a) > 1000:
        #    await bot.send(context, f'答得太长了~', at_sender=True)
        #    return
        q = q.replace('&#91;name&#93;', '[name]')
        q = q.replace('&#91;cqname&#93;', '[cqname]')
        a = a.replace('&#91;name&#93;', '[name]')
        a = a.replace('&#91;cqname&#93;', '[cqname]')
        q = await cqimage(q)
        a = await cqimage(a)
        if 'granbluefantasy.jp' in q or 'granbluefantasy.jp' in a:
            await bot.send(context, '骑空士还挺会玩儿？爬！\n', at_sender=True)
            return
        answersRegex[q] = {}
        Question.replace(
            quest=q,
            rep_group=context['group_id'],
            rep_member=1,
            allow_private=1,
            answer=a,
            creator=context['user_id'],
            create_time=time.time(),
        ).execute()
        await bot.send(context, f'好的我记住了', at_sender=False)
        return
    elif message.startswith('问'):
        msg = message[1:].split('答', 1)
        if len(msg) == 1:
            return
        q, a = msg
        q = q.strip()
        if len(q) == 0:
            return
        if len(a) == 0:
            return
        if len(q) > 200:
            await bot.send(context, f'问得太长了~', at_sender=True)
            return
        if len(a) > 200:
            await bot.send(context, f'答得太长了~', at_sender=True)
            return
        q = q.replace('&#91;name&#93;', '[name] ')
        q = q.replace('&#91;cqname&#93;', '[cqname]')
        a = a.replace('&#91;name&#93;', '[name]')
        a = a.replace('&#91;cqname&#93;', '[cqname]')
        q = await cqimage(q)
        a = await cqimage(a)
        answers[q] = {}
        Question.replace(
            quest=q,
            rep_group=context['group_id'],
            rep_member=1,
            answer=a,
            creator=context['user_id'],
            create_time=time.time(),
        ).execute()
        await bot.send(context, f'好的我记住了', at_sender=False)
        return
    elif message.startswith('不要回答') or message.startswith('删除问题'):
        if context['sender']['role'] == 'member' and context['user_id'] not in bot.config.SUPERUSERS:
            await bot.send(context, f'需要管理员才能删除问题奥~', at_sender=False)
            return
        q = context['raw_message'][4:]
        q = q.strip()
        if q.isdigit():
            line = Question.delete().where(
                Question.id == q
            ).execute()
            if line>0:
                await bot.send(context, f'删除回答ID[{q}]成功', at_sender=False)
                return
            else:
                await bot.send(context, f'查无此回答奥~', at_sender=False)
                return
        else:
            await bot.send(context, f'请输入ID删除回答~', at_sender=False)

    elif message.startswith('查看问题'):
        q = context['raw_message'][4:]
        q = q.strip()
        ans = context['raw_message'] in answers.keys() | context['raw_message'] in answersRegex.keys()
        if ans:
            await bot.send(context, f'我不记得有这个问题', at_sender=False)
            return
        ans = '问题"' + q + '"的回答: '
        flag = False
        for que in Question.select().where(Question.quest == q, Question.rep_member == 1):
            ans +=  '\n' + 'ID:' + str(que.id) + ' | ' + que.answer
            flag = True
        if flag:
            await bot.send(context, ans, at_sender=False)
            return
        else:
            await bot.send(context, f'我不记得有这个问题', at_sender=False)
            return
    elif context['raw_message'] in answers.keys():
        ans = ''
        for que in Question.select().where(Question.quest == context['raw_message'], Question.rep_member == 1, Question.allow_private == 0).order_by(fn.Random()):
            ans = que.answer
            break
        if ans:
            ans = ans.replace('[name]', '[CQ:at,qq='+ str(context['user_id']) +'] ')
            ans = ans.replace('[cqname]', '真红')
            await bot.send(context, ans, at_sender=False)
            return
    else:
        flag = False
        q = ''
        for key in answersRegex:
            if key in context['raw_message']:
                q = key
                flag = True
                break
        if flag:
            ans = ''
            for que in Question.select().where(Question.quest == q, Question.rep_member == 1, Question.allow_private == 1).order_by(fn.Random()):
                ans = que.answer
                break
            if ans:
                ans = ans.replace('[name]', '[CQ:at,qq='+ str(context['user_id']) +'] ')
                ans = ans.replace('[cqname]', '真红')
                await bot.send(context, ans, at_sender=False)
                return  

