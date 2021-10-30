import time
import _thread
import pytz
import os
import re
import asyncio

from datetime import datetime
from nonebot import get_bot
from nonebot import CommandSession, MessageSegment
from nonebot import permission as perm
from peewee import fn
from .data import Msg
from hoshino.service import Service, priv as Priv

sv = Service('seek-msg', manage_priv=Priv.ADMIN, enable_on_default=False)


@sv.on_message('group')
async def handle(bot, context):

    message = context['raw_message']
    if message.startswith('历史消息'):
        msg = message.split('-', 1)
        a = ''
        s = ''
        if len(msg) == 1:
            a = 0
            s = 10
        else:
            strs = re.split(',|，',msg[1])
            #strs = msg[1].split('[，,]', 1)
            if len(strs) > 1:
                s = strs[1]
            if len(s) == 0:
                s = '1'
            a = strs[0]
            a = a.strip()
            s = s.strip()
            if (a.isdigit() and s.isdigit()):
                a = int(a)
                s = int(s)
            else:
                await bot.send(context, f'"-"后第一位数字是消息索引；"，"后第一位是查几条消息', at_sender=False)
                return
        if s > 10:
            await bot.send(context, f'当前最多查询10条消息', at_sender=False)
            return
        bott = get_bot()
        idx = 0
        reply = ''
        for qu in Msg.select().where(Msg.qgroup == context['group_id']).order_by(Msg.create_time.desc()).limit(s).offset(a):
            ret = ''
            if '[CQ:record,' in qu.message and s > 1:
                ret = '语音消息，请单独输入索引查看...'
            else:
                ret = qu.message
            ppl = await bott.get_group_member_info(group_id=context['group_id'], user_id=qu.qid, no_cache=False)
            idx += 1
            nam = ''
            if len(ppl['card']) == 0:
                nam = ppl['nickname']
            else:
                nam = ppl['card']
            reply += '\n' + str(idx) + '. ' + nam + ' : ' + ret
        reply = '获取到最近' + str(idx) +'条消息：' + reply

        message_id = await bot.send(context, reply, at_sender=True)
        
        
        await asyncio.create_task(delay_del(message_id=message_id['message_id']))

        idx = 0
        return
    elif message.startswith('查看消息'):
        if len(context.message) <= 2:
            return
        qid = 0
        if context.message[1].type == 'at':
            qid = context.message[1].data['qq']
        else:
            return
        strs = message.split('[', 1)
        q = strs[0]
        a = ''
        s = ''
        msg = q.split('-', 1)
        if len(msg) == 1:
            a = 0
            s = 10
        else:
            strs = re.split(',|，',msg[1])
            if len(strs) > 1:
                s = strs[1]
            if len(s) == 0:
                s = '1'
            a = strs[0]
            a = a.strip()
            s = s.strip()
            if (a.isdigit() and s.isdigit()):
                a = int(a)
                s = int(s)
            else:
                await bot.send(context, f'"-"后第一位数字是消息索引；"，"后第一位是查几条消息', at_sender=False)
                return
        if s > 10:
            await bot.send(context, f'当前最多查询10条消息', at_sender=False)
            return
        reply = ''
        bott = get_bot()
        idx = 0
        for qu in Msg.select().where(Msg.qgroup == context['group_id'], Msg.qid == qid).order_by(Msg.create_time.desc()).limit(s).offset(a):
            ret = ''
            if '[CQ:record,' in qu.message and s > 1:
                ret = '语音消息，请单独输入索引查看...'
            else:
                ret = qu.message
            ppl = await bott.get_group_member_info(group_id=context['group_id'], user_id=qu.qid, no_cache=False)
            idx += 1
            nam = ''
            if len(ppl['card']) == 0:
                nam = ppl['nickname']
            else:
                nam = ppl['card']
            reply += '\n' + str(idx) + '. ' + nam + ' : ' + ret
        reply = '获取到最近' + str(idx) +'条消息：' + reply
        message_id = await bot.send(context, reply, at_sender=True)
        await asyncio.create_task(delay_del(message_id=message_id['message_id']))
        idx = 0
        return
    else:
        message = message.replace(',type=flash','')
        Msg.replace(
            message=message,
            qgroup=context['group_id'],
            qid=context['user_id'],
            create_time=time.time()
        ).execute()

@sv.scheduled_job('cron', hour='*')
async def hour_call():
    now = datetime.now(pytz.timezone('Asia/Shanghai'))
    if 2 == now.hour:
        Msg.delete().execute()
    else:
        return

async def delay_del(message_id):
    await asyncio.sleep(60)
    bott = get_bot()
    await bott.delete_msg(message_id=message_id)
