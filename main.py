import discord
from discord.ext import commands
from discord.utils import get
from keep_alive import keep_alive
from replit import db
import os
description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='$', description=description, intents=intents)

teamMemberRole = "Team member"
teamRole = "Teams"
playerRole = "Player"
teamManagerRole = "Team manager/Coach"

def mentionById(id, user):
  if user:
    return "<@{0}>".format(id)
  else:
    return "<@&{0}>".format(id)

@bot.event
async def on_ready():
  print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.group()
async def vbc(ctx):
  if ctx.invoked_subcommand is None:
    await ctx.send(f'Command {ctx.subcommand_passed} is not found. Try $vbc help')

@vbc.command(name='help')
async def _help(ctx):
  await ctx.message.channel.send("""Welcome to VolyB Championship Official Bot!
  `$vbc help                                      ` | To see this :smiley:
  `$vbc create team "(team name)" "(abbreviation)"` | Creates a team with the given name. Make sure to add the qoutes.
  `$vbc set roster @Player1 @Player2 @Player3 ... ` | Sets the players in the team, giving them roles. Make sure to mention your teammates and substitudes (up to 10).
  `$vbc set staff @Staff1 @Staff2 @Staff3 ...     ` | Sets the management and coaches of the team, giving them roles. Make sure to mention them (up to 5).
  `$vbc remove team                               ` | Deletes the team.
  `$vbc remove player @Player                     ` | Removes the player from his current team.
  `$vbc remove staff @Person                      ` | Removes the staff from his current team.
  `$vbc quit                                      ` | Makes you quit your current team.
  `$vbc list @Team                                ` | Show list of the players of the given team.
  """)

@vbc.group()
async def create(ctx):
  if ctx.invoked_subcommand is None:
    await ctx.message.channel.send("""Welcome to VolyB Championship Official Bot!
    `$vbc create team "(team name)" "(abbreviation)"` | Creates a team with the given name. Make sure to add the qoutes.""")

@create.command(name='team')
async def _create_team(ctx, name:str, abbr:str):
  if not ('teams' in db.keys()):
    db['teams'] = {};
  if not ('players' in db.keys()):
    db['players'] = {};
  if not ('staff' in db.keys()):
    db['staff'] = {};
  
  author_id = str(ctx.author.id)

  if author_id in db['teams'].keys():
    team = db['teams'][author_id]['name']
    await ctx.message.channel.send(f'Team `{name}` has NOT been created. You already own a team called `{team}`')
  elif author_id in db['players'].keys():
    team = db['players'][author_id]['team']
    await ctx.message.channel.send(f'Team `{name}` has NOT been created. You are already part of a team called `{team}`. If you are not, contact the support team via #💁-support-tickets. @Support Team .')
  else:
    team_role = "{0} ({1})".format(name, abbr)
    role = await ctx.guild.create_role(name=team_role, mentionable=True,hoist=True)

    await ctx.message.author.add_roles(role)
    await ctx.message.author.add_roles(discord.utils.get(ctx.message.author.guild.roles, name=teamRole))
    await ctx.message.author.add_roles(discord.utils.get(ctx.message.author.guild.roles, name=teamMemberRole))
    await ctx.message.author.add_roles(discord.utils.get(ctx.message.author.guild.roles, name=teamManagerRole))

    db['teams'][author_id] = {'name': team_role, 'players': []}
    db['players'][author_id] = {'team': team_role}

    guild = ctx.guild
    admin_role = get(ctx.guild.roles, name=team_role)
    cat = discord.utils.get(ctx.guild.categories, name="Team channels")
    voice = await guild.create_voice_channel("{0}".format(team_role), overwrites={
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        admin_role: discord.PermissionOverwrite(read_messages=True)
    }, category=cat)
    text = await guild.create_text_channel("{0}".format(team_role), overwrites={
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True),
        admin_role: discord.PermissionOverwrite(read_messages=True)
    }, category=cat)

    teamMention = mentionById(admin_role.id, False)
    authorMention = mentionById(ctx.author.id, True)
    await ctx.message.channel.send(f'Team {teamMention} has been created with abbreviation `{abbr}` by {authorMention}.')

@vbc.group()
async def set(ctx):
  if ctx.invoked_subcommand is None:
    await ctx.message.channel.send("""Welcome to VolyB Championship Official Bot!
    `$vbc create team "(team name)" "(abbreviation)"` | Creates a team with the given name. Make sure to add the qoutes.""")

@set.command(name='roster')
async def _set_roster(ctx, *players):
  if len(players) > 10:
    await ctx.message.channel.send(f'Error: Too many player. Your roster can be up to 10 people.')
    return
  try:
    await ctx.message.channel.send(f'Setting the team up, please wait.')
    team_role = db['teams'][str(ctx.author.id)]['name']
    failed = False
    for player in players:
      player_id = player[3:-1]
      if (player_id in db['teams'].keys() and db['teams'][player_id]['name'] != team_role) or (player_id in db['players'].keys() and db['players'][player_id]['team'] != team_role):
        playerMention = mentionById(player_id, True)
        await ctx.message.channel.send(f'{playerMention} has another team already.')
        failed = True
    if not failed:
      for player_id in db['teams'][str(ctx.author.id)]['players']:
        user = await ctx.guild.fetch_member(player_id)
        await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
      db['teams'][str(ctx.author.id)]['players'] = []
      for player in players:
        player_id = player[3:-1]
        user = await ctx.guild.fetch_member(player_id)
        await user.add_roles(discord.utils.get(user.guild.roles, name=team_role))
        await user.add_roles(discord.utils.get(user.guild.roles, name=teamMemberRole))
        await user.add_roles(discord.utils.get(user.guild.roles, name=playerRole))
        await user.add_roles(discord.utils.get(user.guild.roles, name=teamRole))
        db['players'][player_id] = {'team': team_role}
        db['teams'][str(ctx.author.id)]['players'].append(player_id)
      teamMention = mentionById(get(ctx.guild.roles, name=team_role).id, False)
      playersMention = []
      for player_id in db['teams'][str(ctx.author.id)]['players']:
        playersMention.append(mentionById(player_id, True))
      playersMention = ', '.join(playersMention)
      await ctx.message.channel.send(f'{teamMention}\'s roster was set to {playersMention}.')
  except:
    await ctx.message.channel.send(f'Something went wrong. Look if there is a blank space between every 2 players and try again.')

@set.command(name='staff')
async def _set_roster(ctx, *staff):
  if len(staff) > 5:
    await ctx.message.channel.send(f'Error: Too many people. Your management can be up to 5 people.')
    return
  try:
    await ctx.message.channel.send(f'Setting the management up, please wait.')
    team_role = db['teams'][str(ctx.author.id)]['name']
    failed = False
    for person in staff:
      staff_id = person[3:-1]
      if (staff_id in db['staff'].keys() and db['staff'][staff_id]['team'] != team_role):
        staffMention = mentionById(staff_id, True)
        await ctx.message.channel.send(f'{staffMention} has another team already.')
        failed = True
    if not failed:
      peopleMention = []
      for person in staff:
        staff_id = person[3:-1]
        peopleMention.append(mentionById(staff_id, True))
        user = await ctx.guild.fetch_member(staff_id)
        await user.add_roles(discord.utils.get(user.guild.roles, name=team_role))
        await user.add_roles(discord.utils.get(user.guild.roles, name=teamMemberRole))
        await user.add_roles(discord.utils.get(user.guild.roles, name=teamManagerRole))
        await user.add_roles(discord.utils.get(user.guild.roles, name=teamRole))
        db['staff'][staff_id] = {'team': team_role}
      teamMention = mentionById(get(ctx.guild.roles, name=team_role).id, False)
      peopleMention = ', '.join(peopleMention)
      await ctx.message.channel.send(f'{teamMention}\'s management and coaches were set to {peopleMention}.')
  except:
    await ctx.message.channel.send(f'Something went wrong. Look if there is a blank space between every 2 people and try again.')

@vbc.group()
async def remove(ctx):
  if ctx.invoked_subcommand is None:
    await ctx.message.channel.send("""Welcome to VolyB Championship Official Bot!
  `$vbc remove team                               ` | Deletes the team.
  `$vbc remove player @Player                     ` | Removes the player from his current team.
  `$vbc remove staff @Person                      ` | Removes the staff from his current team.""")

@remove.command('team')
async def team(ctx):
  team_role = db['teams'][str(ctx.author.id)]['name']
  for player in db['players']:
    if db['players'][player]['team'] == team_role:
      user = await ctx.guild.fetch_member(player)
      await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
      await user.remove_roles(discord.utils.get(user.guild.roles, name=teamMemberRole))
      await user.remove_roles(discord.utils.get(user.guild.roles, name=playerRole))
      await user.remove_roles(discord.utils.get(user.guild.roles, name=teamRole))
      db['players'].pop(player)
  for person in db['staff']:
    if db['staff'][person]['team'] == team_role:
      user = await ctx.guild.fetch_member(person)
      await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
      await user.remove_roles(discord.utils.get(user.guild.roles, name=teamMemberRole))
      await user.remove_roles(discord.utils.get(user.guild.roles, name=teamRole))
      await user.remove_roles(discord.utils.get(user.guild.roles, name=teamManagerRole))
      db['staff'].pop(person)
  
  user = ctx.author
  await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
  await user.remove_roles(discord.utils.get(user.guild.roles, name=teamRole))
  await user.remove_roles(discord.utils.get(user.guild.roles, name=teamMemberRole))
  await user.remove_roles(discord.utils.get(user.guild.roles, name=teamManagerRole))
  db['teams'].pop(str(ctx.author.id))

  voice = discord.utils.get(ctx.guild.voice_channels, name=team_role)
  text = discord.utils.get(ctx.guild.text_channels, name=''.join(filter((lambda x: x.isalpha() or x=='-'), team_role.replace(" ","-"))).lower())
  await voice.delete()
  await text.delete()

  role_object = discord.utils.get(ctx.message.guild.roles, name=team_role)
  await role_object.delete()

  await ctx.message.channel.send(f'{team_role} has been deleted.')

@remove.command('player')
async def player(ctx, player):
  team_role = db['teams'][str(ctx.author.id)]['name']
  if db['players'][player]['team'] == team_role:
    user = await ctx.guild.fetch_member(player)
    await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
    db['players'].pop(player)
    db['teams'][str(ctx.author.id)]['players'].remove(player)

    playerMention = mentionById(player, True)
    teamMention = mentionById(team_role, False)
    await ctx.message.channel.send(f'{playerMention} has been removed from {teamMention}.')
  else:
    playerMention = mentionById(player, True)
    teamMention = mentionById(team_role, False)
    await ctx.message.channel.send(f'{playerMention} is not part of {teamMention} so you cannot remove him from the team.')

@remove.command('staff')
async def staff(ctx, person):
  team_role = db['teams'][str(ctx.author.id)]['name']
  if db['staff'][person]['team'] == team_role:
    user = await ctx.guild.fetch_member(person)
    await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
    db['staff'].pop(person)
    personMention = mentionById(person, True)
    teamMention = mentionById(team_role, False)
    await ctx.message.channel.send(f'{personMention} has been removed from {teamMention}.')
  else:
    personMention = mentionById(person, True)
    teamMention = mentionById(team_role, False)
    await ctx.message.channel.send(f'{personMention} is not part of {teamMention} so you cannot remove him from the team.')

@vbc.command('quit')
async def quit(ctx):
  if str(ctx.author.id) in db['teams']:
    team_role = db['teams'][str(ctx.author.id)]['name']
    playerMention = mentionById(str(ctx.author.id), True)
    teamMention = mentionById(team_role, False)
    await ctx.message.channel.send(f'{playerMention} is the owner of {teamMention}. Owners cannot quit their own teams.')
    return
  
  if not (db['staff'][str(ctx.author.id)] is None):
    team_role = db['staff'][str(ctx.author.id)]['team']
    user = await ctx.guild.fetch_member(str(ctx.author.id))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=teamMemberRole))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=teamRole))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=teamManagerRole))
    db['staff'].pop(str(ctx.author.id))
  elif not (db['players'][str(ctx.author.id)] is None):
    team_role = db['staff'][str(ctx.author.id)]['team']
    user = await ctx.guild.fetch_member(str(ctx.author.id))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=team_role))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=teamMemberRole))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=teamRole))
    await user.remove_roles(discord.utils.get(user.guild.roles, name=playerRole))
    db['players'].pop(str(ctx.author.id))
  else:
    playerMention = mentionById(str(ctx.author.id), True)
    await ctx.message.channel.send(f'{playerMention} is not part of any team.')

@vbc.command('list')
async def list(ctx, teamRole:discord.Role):
    teamName = teamRole.name
    teamMention = teamRole.mention
    text = ''
    await ctx.message.channel.send(f'Team {teamMention}:')
    for owners in db['teams']:
        if db['teams'][owners]['name'] == teamName:
            mention = mentionById(owners, True)
            text = text + (f'`  Owner:` {mention}\n`Players:` \n')
            for player in db['teams'][owners]['players']:
              mention = mentionById(player, True)
              text = text + f'`        ` {mention}\n'
            text = text + (f'`  Staff:`\n')
            for staff in db['staff']:
              if db['staff'][staff]['team'] == teamName:
                mention = mentionById(staff, True)
                text = text + f'`        ` {mention}\n'
            break
    await ctx.message.channel.send(text)

# dq team admin
# opgg setup

keep_alive()
bot.run(os.getenv('TOKEN'))