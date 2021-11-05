import os
from dotenv import load_dotenv
from Classes import Queue

import discord
from discord.ext import commands

import pafy
import asyncio
import datetime

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
personal_server_name = os.getenv('DISCORD_GUILD')

# global_variables
client = commands.Bot(command_prefix = "-")
ffmpeg_opts = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}
song_queue = Queue()
song_titles = Queue()
song_urls = Queue()

# functions
def is_bot_user(ctx):
	user = ctx.author
	for role in user.roles:
		if role.name == "bot_user":
			return True
	return False

def check_ctx(ctx):
	resp = False
	user = ctx.author
	server = ctx.guild
	if user.voice is not None:
		user_voice_channel = user.voice.channel
		bot_voice_channel = server.voice_client.channel
		if user_voice_channel == bot_voice_channel:
			resp = True

	return resp

def true_message(message):
	return True

# client_events
@client.event
async def on_ready():
	print('Logged on as {0}!'.format(client.user))

@client.event
async def on_message(message):
	if message.author != client.user and message.content != "":
		print('{0.author}: {0.content}'.format(message))
	if not isinstance(message.channel, discord.channel.DMChannel):
		await client.process_commands(message)

@client.event
async def on_voice_state_update(member, before, after):
	if member == client.user:
		if after.channel is None:
			song_queue.empty()
			song_titles.empty()
			song_urls.empty()
			for voice_client in client.voice_clients:
				if voice_client.guild == member.guild:
					await voice_client.disconnect()
					return
					
# bot_commands
@client.command()
async def clear(ctx, argc = None):
	if is_bot_user(ctx):
		deleted = []
		if argc is None:
			today = datetime.datetime.utcnow()
			yesterday = today - datetime.timedelta(days = 1)
			deleted = await ctx.channel.purge(after = yesterday)
		else:
			deleted = await ctx.channel.purge(limit = int(argc) + 1, check = true_message)

		messages_deleted = len(deleted)

		await ctx.send('Successfully deleted {0} message(s)'.format(messages_deleted - 1))
		print('{0}: successfully deleted {1} message(s)'.format(client.user, messages_deleted))
	pass

@client.command()
async def join(ctx):
	user = ctx.author
	server = ctx.guild
	voice_client = server.voice_client

	if user.voice is None:
		await ctx.send("You must be connected to a voice channel to use that command")
		print('{0}: {1} is not connected to any voice channel'.format(client.user, user))
		return

	if voice_client is not None:
		await ctx.send('Already connected to {0}'.format(voice_client.channel.mention))
		print('{0}: Already connected to {1}'.format(client.user, voice_client.channel.name))
		return

	voice_channel = user.voice.channel
	await voice_channel.connect()
	print('{0}: connected to {1} in server: {2}'.format(client.user, voice_channel.name, server))

async def play_song(ctx, voice_client):
	if not song_queue.is_empty():
		audio = song_queue.dequeue()
		title = song_titles.dequeue()
		url = song_urls.dequeue()
		await ctx.send('Playing: {0}\n URL: {1}'.format(title, url))
		print('{0}: Playing: {1}, URL: {2}'.format(client.user, title, url))
		voice_client.play(discord.FFmpegPCMAudio(audio, **ffmpeg_opts), after = lambda e : asyncio.run_coroutine_threadsafe(play_song(ctx, voice_client), client.loop))

@client.command()
async def play(ctx, argc = None):
	await ctx.message.delete()
	user = ctx.author
	server = ctx.guild
	voice_client = server.voice_client

	if voice_client is None:
		await ctx.send("I must be connected to a voice channel to play songs")
		print('{0}: not connected to a voice channel'.format(client.user, user))
		return

	if not check_ctx(ctx):
		await ctx.send("You must be in the same voice channel as me to use that command")
		print('{0}: {1} is not in the same voice channel'.format(client.user, user))
		return
	
	if argc is None:
		await ctx.send("No song was mentioned")
		print('{0}: no url was passed'.format(client.user))
		return

	link = argc
	video = pafy.new(link, basic = False)

	if video is None:
		await ctx.send("Url not found")
		print('{0}: error, url not found'.format(client.user))
		return

	audio = video.getbestaudio().url
	title = video.title
	url = link

	if voice_client.is_playing() or voice_client.is_paused():
		await ctx.send('Queueing: {0}'.format(title))
		song_queue.enqueue(audio)
		song_titles.enqueue(title)
		song_urls.enqueue(url)
	else:
		song_queue.enqueue(audio)
		song_titles.enqueue(title)
		song_urls.enqueue(url)
		await play_song(ctx, voice_client)

	pass

@client.command()
async def pause(ctx):
	if not check_ctx(ctx):
		await ctx.send("You must be in the same voice channel as me to use that command")
		print('{0}: {1} is not in the same voice channel'.format(client.user, ctx.author))
		return

	server = ctx.guild
	voice_client = server.voice_client

	if not voice_client.is_playing():
		await ctx.send("Nothing to pause")
		print('{0}: nothing to pause'.format(client.user))
		return

	voice_client.pause()
	await ctx.send('{0} paused the song'.format(ctx.author))
	print('{0}: {1} paused the song'.format(client.user, ctx.author))

@client.command()
async def resume(ctx):
	if not check_ctx(ctx):
		await ctx.send("You must be in the same voice channel as me to use that command")
		print('{0}: {1} is not in the same voice channel'.format(client.user, ctx.author))
		return

	server = ctx.guild
	voice_client = server.voice_client

	if not voice_client.is_paused():
		await ctx.send("Nothing to resume")
		print('{0}: nothing to resume'.format())

	voice_client.resume()
	await ctx.send('{0} resumed the song'.format(ctx.author))
	print('{0}: {1} resumed the song'.format(client.user, ctx.author))
	pass

@client.command()
async def skip(ctx):
	if not check_ctx(ctx):
		await ctx.send("You must be in the same voice channel as me to use that command")
		print('{0}: {1} is not in the same voice channel'.format(client.user, ctx.author))
		return

	server = ctx.guild
	voice_client = server.voice_client

	if not voice_client.is_paused():
		if not voice_client.is_playing():
			await ctx.send("Nothing to skip")
			print('{0}: nothing to skip'.format(client.user))

	voice_client.stop()
	await ctx.send('{0} skipped the song'.format(ctx.author))
	await play_song(ctx, voice_client)
	pass

@client.command()
async def queue(ctx):
	song_list = song_queue.list()
	song_titles_list = song_titles.list()
	song_urls_list = song_urls.list()

	if len(song_list) == 0:
		await ctx.send("Nothing in queue")
		print('{0}: Nothing in queue'.format(client.user))
		return
	
	print('{0}: Printing song queue'.format(client.user))

	output = ""
	for count in range(0, len(song_list)):
		output = str(count + 1) + ". " + str(song_titles_list[count]) + "\nURL: " + str(song_urls_list[count]) + "\n"
	
	await ctx.send("```" + output + "```")
	pass

@client.command()
async def empty(ctx):
	if not check_ctx(ctx):
		await ctx.send("You must be in the same voice channel as me to use that command")
		print('{0}: {1} is not in the same voice channel'.format(client.user, ctx.author))
		return

	if song_queue.is_empty():
		await ctx.send("Queue already empty")
		print('{0}: queue already empty'.format(client.user))

	song_queue.empty()
	song_titles.empty()
	song_urls.empty()
	await ctx.send('{0} emptied song queue'.format(ctx.author))
	print('{0}: {1}: emptied song queue'.format(client.user, ctx.author))
	pass
	

@client.command()
async def leave(ctx):
	if ctx.me.voice is None:
		print('{0}: error disconnecting, not connected to any channel'.format(client.user))
	else:
		if not check_ctx(ctx):
			await ctx.send("You must be in the same voice channel as me to use that command")
			print('{0}: {1} is not in the same voice channel'.format(client.user, ctx.author))
			return

		server = ctx.guild
		voice_client = server.voice_client

		song_queue.empty()
		song_titles.empty()
		song_urls.empty()
		await voice_client.disconnect()
		print('{0}: disconnected from {1} in server: {2}'.format(client.user, voice_client.channel.name, ctx.guild))
	pass

client.run(token)
