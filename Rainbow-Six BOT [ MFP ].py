import discord
import asyncio
import os
from discord.ext import commands
import urllib
from urllib.request import URLError
from urllib.request import HTTPError
from urllib.request import urlopen
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from urllib.parse import quote
import re # Regex for youtube link
import warnings
import requests
import unicodedata
from tqdm import tqdm

operatoriconURLDict = dict()

# Scrape Rainbow Six Siege's Operator's icon before start
unisoftURL = "https://www.ubisoft.com"
rainbowSixSiegeOperatorIconURL = "https://www.ubisoft.com/en-gb/game/rainbow-six/siege/game-info/operators"
html = requests.get(rainbowSixSiegeOperatorIconURL).text
bs = BeautifulSoup(html,'html.parser')

#Get oprators' pages with ccid
operatorListDiv = bs.findAll('div',{'ccid' : re.compile('[0-9A-Za-z]*')})
print("Initiating Rainbow Six Siege Operators' Information....")
for ind in tqdm(range(0,len(operatorListDiv))):
    operatormainURL = operatorListDiv[ind].a['href']
    #Get Operator's name
    operatorname = operatormainURL.split('/')[-1]
    #Open URL : each operator's pages
    html2 = requests.get(unisoftURL + operatormainURL).text
    bs2 = BeautifulSoup(html2, 'html.parser')
    operatoriconURL = bs2.find('div',{'class' : "operator__header__icons__names"}).img['src']
    operatoriconURLDict[operatorname] = operatoriconURL


token = 'NzA3NTQ4OTcxODk1MDk1MzM3.XrKdfQ.6U3-jwAu2dsUxwS_ycY3pDlb9qI'

client = discord.Client() # Create Instance of Client. This Client is discord server's connection to Discord Room
def deleteTags(htmls):
    for a in range(len(htmls)):
        htmls[a] = re.sub('<.+?>','',str(htmls[a]),0).strip()
    return htmls

#Strip accents in english : Like a in jäger
def convertToNormalEnglish(text):
    return ''.join(char for char in unicodedata.normalize('NFKD', text) if unicodedata.category(char) != 'Mn')

#r6stats 서버에서 크롤링을 막은듯하다
r6URL = "https://r6stats.com"
playerSite = 'https://www.r6stats.com/search/'


@client.event # Use these decorator to register an event.
async def on_ready(): # on_ready() event : when the bot has finised logging in and setting things up
    await client.change_presence(status=discord.Status.online, activity=discord.Game("Rainbow-Six [ MFP ]"))
    print("New log in as {0.user}".format(client))

@client.event
async def on_message(message): # on_message() event : when the bot has recieved a message
    #To user who sent message
    # await message.author.send(msg)
    print(message.content)
    if message.author == client.user:
        return

    if message.content.startswith("!레식전적"):

        # Get player nickname and parse page
        playerNickname = ''.join((message.content).split(' ')[1:])
        html = requests.get(playerSite + playerNickname + '/pc/').text
        bs = BeautifulSoup(html, 'html.parser')

        # 한번에 검색 안되는 경우에는 해당 반환 리스트의 길이 존재. -> bs.find('div',{'class' : 'results'}

        if bs.find('div', {'class': 'results'}) == None:
            # Get latest season's Rank information
            latestSeason = bs.find('div', {'class': re.compile('season\-rank operation\_[A-Za-z_]*')})

            # if player nickname not entered
            if len(message.content.split(" ")) == 1:
                embed = discord.Embed(title="플레이어 이름이 입력되지 않았습니다", description="", color=0x5CD1E5)
                embed.add_field(name="Error : Player name not entered" + playerNickname,
                                value="To use command : !레식전적 (nickname)")
                embed.set_footer(text='Service provided by Hoplin.',
                                 icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                await message.channel.send("Error : Player name not entered ", embed=embed)

            # search if it's empty page
            elif latestSeason == None:
                embed = discord.Embed(title="해당 이름을 가진 플레이어가 존재하지않습니다.", description="", color=0x5CD1E5)
                embed.add_field(name="Error : Can't find player name " + playerNickname,
                                value="Please check player's nickname")
                embed.set_footer(text='Service provided by Hoplin.',
                                 icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                await message.channel.send("Error : Can't find player name " + playerNickname, embed=embed)

            # Command entered well
            else:
                # r6stats profile image
                r6Profile = bs.find('div', {'class': 'main-logo'}).img['src']

                # player level
                playerLevel = bs.find('span', {'class': 'quick-info__value'}).text.strip()

                RankStats = bs.find('div', {'class': 'card stat-card block__ranked horizontal'}).findAll('span', {
                    'class': 'stat-count'})
                # Get text from <span> values
                for info in range(len(RankStats)):
                    RankStats[info] = RankStats[info].text.strip()
                # value of variable RankStats : [Timeplayed, Match Played,kills per matchm, kills,death, KDA Rate,Wins,Losses,W/L Rate]

                # latest season tier medal
                lastestSeasonRankMedalLocation = latestSeason.div.img['src']
                # latest Season tier
                lastestSeasonRankTier = latestSeason.div.img['alt']
                # latest season operation name
                OperationName = latestSeason.find('div', {'class': 'meta-wrapper'}).find('div', {
                    'class': 'operation-title'}).text.strip()
                # latest season Ranking
                latestSeasonRanking = latestSeason.find('div', {'class': 'rankings-wrapper'}).find('span', {
                    'class': 'ranking'})

                # if player not ranked, span has class not ranked if ranked span get class ranking
                if latestSeasonRanking == None:
                    latestSeasonRanking = bs.find('span', {'class': 'not-ranked'}).text.upper()
                else:
                    latestSeasonRanking = latestSeasonRanking.text

                # Add player's MMR Rank MMR Information
                playerInfoMenus = bs.find('a', {'class': 'player-tabs__season_stats'})['href']
                mmrMenu = r6URL + playerInfoMenus
                html = requests.get(mmrMenu).text
                bs = BeautifulSoup(html, 'html.parser')

                # recent season rank box
                # Rank show in purpose : America - Europe - Asia. This code only support Asia server's MMR
                getElements = bs.find('div', {'class': 'card__content'})  # first elements with class 'card__contet is latest season content box

                for ckAsia in getElements.findAll('div', {'class': 'season-stat--region'}):
                    checkRegion = ckAsia.find('div',{'class' : 'season-stat--region-title'}).text
                    if checkRegion == "Asia":
                        getElements = ckAsia
                        break
                    else:
                        pass

                # Player's Tier Information
                latestSeasonTier = getElements.find('img')['alt']
                # MMR Datas Info -> [Win,Losses,Abandon,Max,W/L,MMR]
                mmrDatas = []
                for dt in getElements.findAll('span', {'class': 'season-stat--region-stats__stat'}):
                    mmrDatas.append(dt.text)

                embed = discord.Embed(title="Rainbow Six Siege player search from r6stats", description="",
                                      color=0x5CD1E5)
                embed.add_field(name="Player search from r6stats", value=playerSite + playerNickname + '/pc/',
                                inline=False)
                embed.add_field(name="Player's basic information",
                                value="Ranking : #" + latestSeasonRanking + " | " + "Level : " + playerLevel,
                                inline=False)
                embed.add_field(name="Latest season information | Operation : " + OperationName,
                                value=
                                "Tier(Asia) : " + latestSeasonTier + " | W/L : " + mmrDatas[0] + "/" + mmrDatas[
                                    1] + " | " + "MMR(Asia) : " + mmrDatas[-1],
                                inline=False)

                embed.add_field(name="Total Play Time", value=RankStats[0], inline=True)
                embed.add_field(name="Match Played", value=RankStats[1], inline=True)
                embed.add_field(name="Kills per match", value=RankStats[2], inline=True)
                embed.add_field(name="Total Kills", value=RankStats[3], inline=True)
                embed.add_field(name="Total Deaths", value=RankStats[4], inline=True)
                embed.add_field(name="K/D Ratio", value=RankStats[5], inline=True)
                embed.add_field(name="Wins", value=RankStats[6], inline=True)
                embed.add_field(name="Losses", value=RankStats[7], inline=True)
                embed.add_field(name="W/L Ratio", value=RankStats[8], inline=True)
                embed.set_thumbnail(url=r6URL + r6Profile)
                embed.set_footer(text='Service provided by Hoplin.',
                                 icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                await message.channel.send("Player " + playerNickname + "'s stats search", embed=embed)
        else:
            searchLink = bs.find('a', {'class': 'result'})
            if searchLink == None:
                embed = discord.Embed(title="해당 이름을 가진 플레이어가 존재하지않습니다.", description="", color=0x5CD1E5)
                embed.add_field(name="Error : Can't find player name " + playerNickname,
                                value="Please check player's nickname")
                embed.set_footer(text='Service provided by Hoplin.',
                                 icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                await message.channel.send("Error : Can't find player name " + playerNickname, embed=embed)
            else:
                searchLink = r6URL + searchLink['href']
                html = requests.get(searchLink).text
                bs = BeautifulSoup(html, 'html.parser')
                # Get latest season's Rank information
                latestSeason = bs.findAll('div', {'class': re.compile('season\-rank operation\_[A-Za-z_]*')})[0]

                # if player nickname not entered
                if len(message.content.split(" ")) == 1:
                    embed = discord.Embed(title="플레이어 이름이 입력되지 않았습니다", description="", color=0x5CD1E5)
                    embed.add_field(name="Error : Player name not entered" + playerNickname,
                                    value="To use command : !레식전적 (nickname)")
                    embed.set_footer(text='Service provided by Hoplin.',
                                     icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                    await message.channel.send("Error : Player name not entered ", embed=embed)

                # search if it's empty page
                elif latestSeason == None:
                    embed = discord.Embed(title="해당 이름을 가진 플레이어가 존재하지않습니다.", description="", color=0x5CD1E5)
                    embed.add_field(name="Error : Can't find player name " + playerNickname,
                                    value="Please check player's nickname")
                    embed.set_footer(text='Service provided by Hoplin.',
                                     icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                    await message.channel.send("Error : Can't find player name " + playerNickname, embed=embed)

                # Command entered well
                else:

                    # r6stats profile image
                    r6Profile = bs.find('div', {'class': 'main-logo'}).img['src']

                    # player level
                    playerLevel = bs.find('span', {'class': 'quick-info__value'}).text.strip()

                    RankStats = bs.find('div', {'class': 'card stat-card block__ranked horizontal'}).findAll('span', {
                        'class': 'stat-count'})
                    # Get text from <span> values
                    for info in range(len(RankStats)):
                        RankStats[info] = RankStats[info].text.strip()
                    # value of variable RankStats : [Timeplayed, Match Played,kills per matchm, kills,death, KDA Rate,Wins,Losses,W/L Rate]

                    # latest season tier medal
                    lastestSeasonRankMedalLocation = latestSeason.div.img['src']
                    # latest Season tier
                    lastestSeasonRankTier = latestSeason.div.img['alt']
                    # latest season operation name
                    OperationName = latestSeason.find('div', {'class': 'meta-wrapper'}).find('div', {
                        'class': 'operation-title'}).text.strip()
                    # latest season Ranking
                    latestSeasonRanking = latestSeason.find('div', {'class': 'rankings-wrapper'}).find('span', {
                        'class': 'ranking'})

                    # if player not ranked, span has class not ranked if ranked span get class ranking
                    if latestSeasonRanking == None:
                        latestSeasonRanking = bs.find('span', {'class': 'not-ranked'}).text.upper()
                    else:
                        latestSeasonRanking = latestSeasonRanking.text

                    #Add player's MMR Rank MMR Information
                    playerInfoMenus = bs.find('a', {'class' : 'player-tabs__season_stats'})['href']
                    mmrMenu = r6URL + playerInfoMenus
                    html = requests.get(mmrMenu).text
                    bs = BeautifulSoup(html, 'html.parser')

                    #recent season rank box
                    # Rank show in purpose : America - Europe - Asia. This code only support Asia server's MMR
                    getElements = bs.find('div', {'class': 'card__content'})  # first elements with class 'card__contet is latest season content box

                    for ckAsia in getElements.findAll('div', {'class': 'season-stat--region'}):
                        checkRegion = ckAsia.find('div', {'class': 'season-stat--region-title'}).text
                        if checkRegion == "Asia":
                            getElements = ckAsia
                            break
                        else:
                            pass
                    # Player's Tier Information
                    latestSeasonTier = getElements.find('img')['alt']
                    # MMR Datas Info -> [Win,Losses,Abandon,Max,W/L,MMR]
                    mmrDatas = []
                    for dt in getElements.findAll('span', {'class': 'season-stat--region-stats__stat'}):
                        mmrDatas.append(dt.text)

                    embed = discord.Embed(title="Rainbow Six Siege player search from r6stats", description="",
                                          color=0x5CD1E5)
                    embed.add_field(name="Player search from r6stats", value=searchLink,
                                    inline=False)
                    embed.add_field(name="Player's basic information",value= "Ranking : #" + latestSeasonRanking + " | " + "Level : " + playerLevel,inline=False)
                    embed.add_field(name="Latest season information | Operation : " + OperationName,
                                    value=
                                    "Tier(Asia) : " + latestSeasonTier + " | W/L : " + mmrDatas[0] + "/"+mmrDatas[1] + " | " + "MMR(Asia) : " + mmrDatas[-1],
                                    inline=False)

                    embed.add_field(name="Total Play Time", value=RankStats[0], inline=True)
                    embed.add_field(name="Match Played", value=RankStats[1], inline=True)
                    embed.add_field(name="Kills per match", value=RankStats[2], inline=True)
                    embed.add_field(name="Total Kills", value=RankStats[3], inline=True)
                    embed.add_field(name="Total Deaths", value=RankStats[4], inline=True)
                    embed.add_field(name="K/D Ratio", value=RankStats[5], inline=True)
                    embed.add_field(name="Wins", value=RankStats[6], inline=True)
                    embed.add_field(name="Losses", value=RankStats[7], inline=True)
                    embed.add_field(name="W/L Ratio", value=RankStats[8], inline=True)
                    embed.set_thumbnail(url=r6URL + r6Profile)
                    embed.set_footer(text='Service provided by Hoplin.',
                                     icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                    await message.channel.send("Player " + playerNickname + "'s stats search", embed=embed)

    if message.content.startswith("!레식오퍼"):
        # operator image dictionary key is lowercase

        # for player's operator Informaiton
        useroperatorInformation = dict()

        playerNickname = ''.join((message.content).split(' ')[1:])
        html = requests.get(playerSite + playerNickname + '/pc/').text
        bs = BeautifulSoup(html, 'html.parser')

        if bs.find('div', {'class': 'results'}) == None:
            # Scrape menu hyperlink : to operator menu
            playerOperator = bs.find('a', {'class': 'player-tabs__operators'})
            playerOperatorMenu = r6URL + playerOperator['href']
            print(playerOperatorMenu)
            # Reopen page
            html = requests.get(playerOperatorMenu).text
            bs = BeautifulSoup(html, 'html.parser')

            embed = discord.Embed(title="Stats by operator", description="Arrange in order of high-play operator",
                                  color=0x5CD1E5)

            embed.add_field(name="To see more stats by operator click link here", value=playerOperatorMenu,
                            inline=False)

            operatorStats = bs.findAll('tr', {'class': 'operator'})

            mostOperator = None

            indNumS = 0
            # statlist -> [operator,kills,deaths,K/D,Wins,Losses,W/L,HeadShots,Melee Kills,DBNO,Playtime]
            for op in operatorStats:
                # discord can show maximum 8 fields
                if indNumS == 7:
                    break
                count = 0
                statlist = []
                if op.td.span.text.split(" ")[-1] == "Recruit":
                    pass
                else:
                    for b in op:
                        statlist.append(b.text)
                    if indNumS == 0:
                        mostOperator = convertToNormalEnglish(statlist[0].lower())
                    embed.add_field(name="Operator Name", value=statlist[0], inline=True)
                    embed.add_field(name="Kills / Deaths", value=statlist[1] + "K / " + statlist[2] + "D", inline=True)
                    embed.add_field(name="Wins / Losses", value=statlist[4] + "W / " + statlist[5] + "L", inline=True)
                    indNumS += 1
            embed.set_thumbnail(url=operatoriconURLDict[mostOperator])
            embed.set_footer(text='Service provided by Hoplin.',
                             icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
            await message.channel.send("Player " + playerNickname + "'s stats search", embed=embed)
        else:
            searchLink = bs.find('a', {'class': 'result'})
            if searchLink == None:
                embed = discord.Embed(title="해당 이름을 가진 플레이어가 존재하지않습니다.", description="", color=0x5CD1E5)
                embed.add_field(name="Error : Can't find player name " + playerNickname,
                                value="Please check player's nickname")
                embed.set_footer(text='Service provided by Hoplin.',
                                 icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                await message.channel.send("Error : Can't find player name " + playerNickname, embed=embed)
            else:
                searchLink = bs.find('a', {'class': 'result'})['href']
                searchLink = r6URL + searchLink
                html = requests.get(searchLink).text
                bs = BeautifulSoup(html, 'html.parser')
                # Scrape menu hyperlink : to operator menu
                playerOperator = bs.find('a', {'class': 'player-tabs__operators'})
                playerOperatorMenu = r6URL + playerOperator['href']
                print(playerOperatorMenu)
                # Reopen page
                html = requests.get(playerOperatorMenu).text
                bs = BeautifulSoup(html, 'html.parser')

                embed = discord.Embed(title="Stats by operator", description="Arrange in order of high-play operator",
                                      color=0x5CD1E5)
                embed.add_field(name="To see more stats by operator click link here", value=playerOperatorMenu,
                                inline=False)

                operatorStats = bs.findAll('tr', {'class': 'operator'})

                mostOperator = None

                indNumS = 0
                # statlist -> [operator,kills,deaths,K/D,Wins,Losses,W/L,HeadShots,Melee Kills,DBNO,Playtime]
                for op in operatorStats:
                    # discord can show maximum 8 fields
                    if indNumS == 7:
                        break
                    count = 0
                    statlist = []
                    if op.td.span.text.split(" ")[-1] == "Recruit":
                        pass
                    else:
                        for b in op:
                            statlist.append(b.text)
                        if indNumS == 0:
                            mostOperator = convertToNormalEnglish(statlist[0].lower())
                        embed.add_field(name="Operator Name", value=statlist[0], inline=True)
                        embed.add_field(name="Kills / Deaths", value=statlist[1] + "K / " + statlist[2] + "D",
                                        inline=True)
                        embed.add_field(name="Wins / Losses", value=statlist[4] + "W / " + statlist[5] + "L",
                                        inline=True)
                        indNumS += 1
                embed.set_thumbnail(url=operatoriconURLDict[mostOperator])
                embed.set_footer(text='Service provided by Hoplin.',
                                 icon_url='https://avatars2.githubusercontent.com/u/45956041?s=460&u=1caf3b112111cbd9849a2b95a88c3a8f3a15ecfa&v=4')
                await message.channel.send("Player " + playerNickname + "'s stats search", embed=embed)
client.run(token)