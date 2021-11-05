import os
from dotenv import load_dotenv
from Classes import Queue

import discord
from discord.ext import commands
from discord import FFmpegPCMAudio

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

# functions
def check(ctx):
	user = ctx.author
	for role in user.roles:
		if role.name == "bot_user":
			return True
	return False

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

# bot_commands
@client.command()
async def clear(ctx, argc = None):
	if check(ctx):
		messages = []
		if argc is None:
			today = datetime.datetime.utcnow()
			yesterday = today - datetime.timedelta(days = 1)
			messages = await ctx.channel.history(after = yesterday).flatten()
		else:
			messages = await ctx.channel.history(limit = int(argc) + 1).flatten()

		messages_deleted = 0
		for message in messages:
			await message.delete()
			messages_deleted+=1

		await ctx.send('Successfully deleted {0} message(s)'.format(messages_deleted - 1))
		print('{0}: successfully deleted {1} message(s)'.format(client.user, messages_deleted))
	pass

@client.command()
async def join(ctx):
	user = ctx.author
	server = ctx.guild
	voice_client = server.voice_client

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
		# await ctx.send('Playing: {0.title}\n {0.url_https}'.format(audio))
		# print('{0}: Playing: {1.title}\n {1.url_https}'.format(client.user, audio))
		voice_client.play(FFmpegPCMAudio(audio, **ffmpeg_opts), after = lambda e : asyncio.run_coroutine_threadsafe(play_song(ctx, voice_client), client.loop))

@client.command()
async def play(ctx, argc = None):
	user = ctx.author
	server = ctx.guild
	voice_client = server.voice_client

	# implement check if user is in channel

	if voice_client is None:
		await ctx.send("I must be connected to a voice channel to play songs")
		print('{0}: not connected to a voice channel'.format(client.user, ctx.author))
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
	if voice_client.is_playing():
		song_queue.enqueue(audio)
	else:
		song_queue.enqueue(audio)
		await play_song(ctx, voice_client)

	pass

@client.command()
async def pause(ctx):
	# implement checks
	server = ctx.guild
	voice_client = server.voice_client
	voice_client.pause()
	await ctx.send("Paused")
	print('{0}: {1} paused the song'.format(client.user, ctx.author))

@client.command()
async def resume(ctx):
	#implement checks
	server = ctx.guild
	voice_client = server.voice_client
	voice_client.resume()

@client.command()
async def skip(ctx):
	#implement checks
	server = ctx.guild
	voice_client = server.voice_client
	voice_client.pause()
	await ctx.send("Skipped")
	await play_song(ctx, voice_client)

@client.command()
async def disconnect(ctx):
	if ctx.me.voice is None:
		print('{0}: error disconnecting, not connected to any channel'.format(client.user))
	else:
		server = ctx.guild
		voice_client = server.voice_client

		# implement check

		song_queue.empty()
		await voice_client.disconnect()
		print('{0}: disconnected from {1} in server: {2}'.format(client.user, voice_client.channel.name, ctx.guild))
	pass

client.run(token)
