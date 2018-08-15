#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Written by: KNO3 IT
# https://www.kno3it.com/
# Contact: contact@kno3it.com

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging, random, psycopg2

host = "localhost"
database = "restyaboard"
user = "restya"
password = ""
telegramToken = ""

def main():
	updater = Updater(token='%s' % telegramToken)
	logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
	
	dispatcher = updater.dispatcher
	
	start_handler = CommandHandler('start', start)
	dispatcher.add_handler(start_handler)
	
	help_handler = CommandHandler('help', start)
	dispatcher.add_handler(help_handler)
	
	boards_handler = CommandHandler("boards", boards)
	dispatcher.add_handler(boards_handler)
	
	idea_handler = CommandHandler("idea", idea, pass_args=True)
	dispatcher.add_handler(idea_handler)
	
	lists_handler = CommandHandler("lists", lists, pass_args=True)
	dispatcher.add_handler(lists_handler)
	
	list_handler = CommandHandler("list", list, pass_args=True)
	dispatcher.add_handler(list_handler)
	
	done_handler = CommandHandler("done", done, pass_args=True)
	dispatcher.add_handler(done_handler)
	
	updater.start_polling()

# Commands

def start(bot, update):
	message = """I am Skippy the Magnificent behold my awesome awesomeness.
	
	/start - You clearly know about this one
	/help - Same as /start
	/boards - list available boards
	/lists [BoardName] - lists all lists on board (or all boards and lists)
	/done <CardID> - marks a card as done by archiving it
	/list <BoardName> [List] - lists all cards on a list with the card IDs for "/done" (default list is "Todo")
	
	/idea <BoardName> <Task> - add a card to the board on the "Todo" list
	"""
	
	bot.send_message(chat_id=update.message.chat_id, text=message)
		
def idea(bot, update, **kwargs):
	args = kwargs['args']
	if len(args) >= 2:
		board = args.pop(0)
		task = " ".join(args)
	
	else:
		bot.send_message(chat_id=update.message.chat_id, text="Invalid command, see /help for more information.")
		return False
	
	addCard(bot, update, board, task)

def boards(bot, update):
	conn = getSqlConn(bot, update)
	if not conn:
		return False
	cur = conn.cursor()
	
	boards = getBoards(cur)
	
	text = ""
	for board in boards:
		text += board[0] + '\n'
		
	bot.send_message(chat_id=update.message.chat_id, text=text)	
	
def lists(bot, update, **kwargs):
	args = kwargs['args']
	conn = getSqlConn(bot, update)
	
	if not conn:
		return False
		
	cur = conn.cursor()
	if len(args) == 0:
		listText = "Boards:\n"
		boards = getBoards(cur)
		for board in boards:
			listText += "\n%s" % board
			boardId = getBoardId(bot, update, cur, board)
				
			for list in getLists(cur, boardId):
				listText += "\n        %s" % list
			listText += "\n"
			
		bot.send_message(chat_id=update.message.chat_id, text=listText)
	else:
		boardName = args[0]
		
		boardId = getBoardId(bot, update, cur, boardName)
		if not boardId:
			return False
			
		
		lists = getLists(cur, boardId)
		
		text = "%s:\n" % getBoardName(cur, boardId)
		for list in lists:
			text += "     %s\n" % list
		
		bot.send_message(chat_id=update.message.chat_id, text=text)
		
def list(bot, update, **kwargs):
	args = kwargs['args']
	if len(args) == 0 or len(args) > 2:
		bot.send_message(chat_id=update.message.chat_id, text="Invalid command, see /help for more information.")
		return False
	if len(args) == 1:
		listName = "Todo"
	else:
		listName = args[1]
		
	boardName = args[0]
	
	
	conn = getSqlConn(bot, update)
	if not conn:
		return False
		
	cur = conn.cursor()
	
	boardId = getBoardId(bot, update, cur, boardName)
	if not boardId:
		return False
		
	listId = getListId(bot, update, cur, boardId, listName)
	
	cards = getCards(bot, update, cur, listId)
	if not cards:
		return False
	
	text = "%s %s:\n" % (getBoardName(cur, boardId), getListName(cur, listId)) 
	for i in range(0, len(cards)):
		cardId = cards[i][0]
		task = cards[i][1]
		text += "    %s) [%s] %s \n" % (i + 1, cardId, task)
		
	bot.send_message(chat_id=update.message.chat_id, text=text)

def done(bot, update, **kwargs):
	args = kwargs['args']
	if len(args) != 1:
		bot.send_message(chat_id=update.message.chat_id, text="Invalid command, see /help for more information.")
		return False
	
	cardId = args[0]
	
	conn = getSqlConn(bot, update)
	if not conn:
		return False
		
	cur = conn.cursor()
	
	card = getCard(bot, update, cur, cardId)
	if not card:
		return False
		
	task, list, board = card
	
	archiveCard(bot, update, cardId)
	
	bot.send_message(chat_id=update.message.chat_id, text="Marking \"%s\" as done on \"%s\" from \"%s\"" % (task, list, board))
	
	
#SQL Stuff Here

def getSqlConn(bot, update):
	try:
		conn_str = "dbname='%s' user='%s' host='%s' password='%s'" % (database, user, host, password)
		conn = psycopg2.connect(conn_str)
		return conn
	except:
		bot.send_message(chat_id=update.message.chat_id, text="The database is unreachable!")
		
def getBoardId(bot, update, cur, boardName):
	sql = "select id from boards where upper(\"name\") like '" + boardName.upper() + "%' and organization_id = 2"
	cur.execute(sql)
	results = cur.fetchall()
	
	if len(results) == 0:
		bot.send_message(chat_id=update.message.chat_id, text="There is no board found by that name!")
		return False
		
	elif len(results) > 1:	
		bot.send_message(chat_id=update.message.chat_id, text="That is an ambiguous board name!")
		return False
	else:
		return results[0][0]

def getBoardName(cur, boardId):
	sql = "select \"name\" from boards where id = %s"
	cur.execute(sql, [boardId])
	results = cur.fetchall()
	
	return results[0][0]

def getTodoListID(bot, update, cur, boardId):
	sql = "select id from lists where board_id = %s and \"name\" = 'Todo' limit 1;" 
	cur.execute(sql, [boardId])
	results = cur.fetchall()
	
	if len(results) == 0:
		bot.send_message(chat_id=update.message.chat_id, text="The board does not appear to have a Todo list to add the card!")
		return False
	else:
		return results[0][0]

def getPosition(cur, listId):
	sql = "SELECT coalesce(max(\"position\"), 0) FROM cards where is_deleted = false and is_archived = false and list_id = %s"
	cur.execute(sql, [listId])
	results = cur.fetchall()
	
	return int(results[0][0]) + 1
	
def getUserId(bot, update, cur, firstName, lastName):
	sql = "select id from users where upper(full_name) like '%" + firstName.upper() + "%' and upper(full_name) like '%" + lastName.upper() + "%'"
	cur.execute(sql)
	results = cur.fetchall()
	
	if len(results) == 0:	
		bot.send_message(chat_id=update.message.chat_id, text="You need to have a Restya account in order to interact with this bot!")
		return False
		
	else:
		return results[0][0]
		
def getUserFullName(cur, userId):
	sql = "select full_name from users where id = %s"
	cur.execute(sql, [userId])
	results = cur.fetchall()
	
	return results[0][0]
	
def addCard(bot, update, boardName, task):
	conn = getSqlConn(bot, update)
	if not conn:
		return False
		
	cur = conn.cursor()
	
	boardId = getBoardId(bot, update, cur, boardName)
	if not boardId:
		return False
		
	listId = getTodoListID(bot, update, cur, boardId)
	if not listId:
		return False
		
	userId = getUserId(bot, update, cur, update.message.from_user.first_name, update.message.from_user.last_name)
	if not userId:
		return False
		
	insertSql = """
		begin;
		INSERT INTO cards (
			created, 
			modified, 
			board_id, 
			list_id, 
			"name", 
			"position", 
			is_archived, 
			attachment_count, 
			checklist_count, 
			checklist_item_count, 
			checklist_item_completed_count, 
			label_count, cards_user_count,
			cards_subscriber_count, 
			card_voter_count, 
			activity_count, 
			user_id, 
			is_deleted, 
			comment_count, 
			is_due_date_notification_sent)
		values (current_timestamp, current_timestamp, %s, %s, %s, %s, false, 0, 0, 0, 0, 0, 0, 0, 0, 0, %s, false, 0, false);
		commit;
	"""
	
	cur.execute(insertSql, [boardId, listId, task, getPosition(cur, listId), userId])
	
	bot.send_message(chat_id=update.message.chat_id, text="\"%s\" has been added to \"%s\" by \"%s\"." % (task, getBoardName(cur, boardId), getUserFullName(cur, userId)))
	conn.commit()
	conn.close()
	
	return True

def getListId(bot, update, cur, boardId, listName):
	sql = "select id from lists where board_id = " + str(boardId) + " and upper(\"name\") like '" + listName.upper() + "%' and is_archived = false and is_deleted = false"
	cur.execute(sql)
	results = cur.fetchall()
	
	if len(results) == 0:
		bot.send_message(chat_id=update.message.chat_id, text="That is not a valid list name!")
		return False
		
	return results[0][0]
	
def getListName(cur, listId):
	sql = "select\"name\" from lists where id = %s"
	cur.execute(sql, [listId])
	results = cur.fetchall()
	
	return results[0][0]
	
def getCards(bot, update, cur, listId):
	sql = "select id, \"name\" from cards where list_id = %s and is_archived = false and is_deleted = false"
	cur.execute(sql, [listId])
	results = cur.fetchall()
	
	if len(results) == 0:
		bot.send_message(chat_id=update.message.chat_id, text="That list contains no active cards!")
		return False
	
	return results
	
def getCard(bot, update, cur, cardId):
	sql = "select \"name\", board_id, list_id from cards where id = %s"
	cur.execute(sql, [cardId])
	results = cur.fetchall()
	
	if len(results) == 0:
		bot.send_message(chat_id=update.message.chat_id, text="There is no active card by that ID!")
		return False
		
	task, boardId, listId = results[0]
	
	list = getListName(cur, listId)
	board = getBoardName(cur, boardId)
		
	return (task, list, board)
	
def archiveCard(bot, update, cardId):
	conn = getSqlConn(bot, update)
	cur = conn.cursor()
	
	updateSql = """
	begin;
	UPDATE cards
	SET is_archived = true
	WHERE id = %s;
	commit;
	"""
	cur.execute(updateSql, [cardId])
	
	conn.commit()
	conn.close()
	
def getLists(cur, boardId):
	sql = "select \"name\" from lists where board_id = %s and is_archived = false and is_deleted = false order by \"name\""
	cur.execute(sql, [boardId])
	results = cur.fetchall()
	
	output = []
	for result in results:
		output += [result[0]]
		
	return output
	
def getBoards(cur):
	sql = "select \"name\" from boards where board_visibility = 1 and is_closed = false order by \"name\";"
	cur.execute(sql)
	results = cur.fetchall()
	
	output = []
	for result in results:
		output += [result[0]]
	
	return output
	
main()