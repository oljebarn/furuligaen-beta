
# A very simple Flask Hello World app for you to get started with...
from flask import Flask, render_template
import pandas as pd
import requests

# Finn nåværende GW

def checkGameweek():
    url3 = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    r3 = requests.get(url3)
    json = r3.json()
    gameweek_df = pd.DataFrame(json['events'])
    iscurrent = gameweek_df[['id', 'is_current']]
    currentGw = iscurrent.loc[(iscurrent.is_current == True)].iat[0,0]
    return currentGw

thisGw = checkGameweek()

def getGwStart():
    gw = checkGameweek()
    liste = [5, 9, 13, 17, 21, 25, 29, 33, 37]
    ferdig = False
    while (ferdig == False):
        for obj in liste:
            if gw < obj:
                return obj - 4
                ferdig = True
    else:
        return 37

# Minus 1 for å treffe index 0
gwStarter = getGwStart()

def gwStart():
    return gwStarter - 1

def gwEnd ():
    gw = gwStarter
    if gw == 37 or gw == 38:
        return 38
    else:
        return gw + 3

# For header i tabell
def gwHeader():
    gwE = gwEnd()
    return "GW " + str(gwStarter) + " -> " + str(gwE)

# Poeng i tabell
thisGw = checkGameweek()

# Auto subs
def getBootstrapTeams():
    url4 = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    r4 = requests.get(url4)
    json = r4.json()
    gameweek_df = pd.DataFrame(json['elements'])
    teams = gameweek_df[['id', 'team', 'element_type']]
    teams.set_index('id', inplace = True)
    return teams



def getGwFixtures():
    url2 = 'https://fantasy.premierleague.com/api/fixtures/?event=' + str(thisGw)
    r2 = requests.get(url2)
    json2 = r2.json()
    fixtures_df = pd.DataFrame(json2)

    hfixtures = fixtures_df[['team_h', 'finished']]

    aFixtures = fixtures_df[['team_a', 'finished']]
    aFixtures.columns = ['team_h', 'finished']

    allFix = hfixtures.append(aFixtures)
    allFix.set_index('team_h', inplace = True)
    return allFix

allFix = getGwFixtures()

def getMinutesPlayed():
    url1 = 'https://fantasy.premierleague.com/api/event/' + str(thisGw) + '/live/'
    r1 = requests.get(url1)
    json1 = r1.json()
    liveElements_df = pd.DataFrame(json1['elements'])
    ids = liveElements_df['id']
    stats_df = pd.DataFrame(liveElements_df['stats'].values.tolist())
    minutes = pd.DataFrame(stats_df['minutes'])

    minutes.insert(0, 'id', ids, True)

    minutes.set_index('id', inplace = True)
    return minutes

teams = getBootstrapTeams()
minutes = getMinutesPlayed()

def didNotPlay(playerId):
    teamId = teams.at[playerId, 'team']
    return minutes.at[playerId, 'minutes'] == 0 and allFix.at[teamId, 'finished']

def getAutoSubs(teamId):
    url4 = 'https://fantasy.premierleague.com/api/entry/' + str(teamId) + '/event/' + str(thisGw) + '/picks/'
    r4 = requests.get(url4)
    json4 = r4.json()
    picks_df = pd.DataFrame(json4['picks'])

    spillerListe = picks_df[['element', 'multiplier', 'is_captain', 'is_vice_captain']]

    minDef = 3
    minMid = 3
    minAtt = 1

    countDef = 0
    countMid = 0
    countAtt = 0

    gk = 1
    defs = 2
    mids = 3
    atts = 4

    keeperbytte = spillerListe.iat[11, 0]

    for obj in spillerListe['element'][0:11]:
        starter = obj
        spillerpos = teams.at[starter, 'element_type']
        spilteIkke = didNotPlay(starter)

        if not spilteIkke:
            if spillerpos == defs:
                countDef += 1
            if spillerpos == mids:
                countMid += 1
            if spillerpos == atts:
                countAtt += 1

    for i in range(len(spillerListe[0:11])):
        starter = spillerListe.iat[i,0]
        spilteIkke = didNotPlay(starter)

        if not spilteIkke:
            break

        spillerpos = teams.at[starter, 'element_type']

        erKaptein = spillerListe.iat[i, 2]

        # sjekke kaptein
        if spilteIkke and erKaptein:
            spillerListe.loc[spillerListe['is_vice_captain'] == True, 'multiplier'] = spillerListe.iat[i, 1]
            spillerListe.iat[i, 1] = 0

        # keeperbytte
        if spillerpos == gk and spilteIkke:
            spillerListe.iat[i,1] = 0
            if not didNotPlay(keeperbytte):
                spillerListe.iat[i, 0], spillerListe.iat[11, 0] = spillerListe.iat[11, 0], spillerListe.iat[i, 0]
                spillerListe.iat[i,1] = 1

        # bytte fra benken
        if spillerpos != gk and spilteIkke:
            spillerListe.iat[i,1] = 0
            if countDef >= minDef and countMid >= minMid and countAtt >= minAtt:
                for j in range (len(spillerListe[12:15])):
                    if not didNotPlay(spillerListe.iat[j,0]):
                        innbytterPos = teams.at[spillerListe.iat[j,0], 'element_type']
                        spillerListe.iat[i,0], spillerListe.iat[j,0] = spillerListe.iat[j,0], spillerListe.iat[i,0]
                        spillerListe.iat[i,1] = 1

                        if innbytterPos == defs:
                            countDef += 1
                        if innbytterPos == mids:
                            countMid += 1
                        if innbytterPos == atts:
                            countAtt += 1
                        break

            if countDef < minDef:
                for j in range (len(spillerListe[12:15])):
                    innbytterPos = teams.at[spillerListe.iat[j,0], 'element_type']
                    if innbytterPos == defs and not didNotPlay(spillerListe.iat[j,0]):
                        innbytterPos = teams.at[spillerListe.iat[j,0], 'element_type']
                        spillerListe.iat[i,0], spillerListe.iat[j,0] = spillerListe.iat[j,0], spillerListe.iat[i,0]
                        spillerListe.iat[i,1] = 1
                        countDef += 1
                        break

            if countMid < minMid:
                for j in range (len(spillerListe[12:15])):
                    innbytterPos = teams.at[spillerListe.iat[j,0], 'element_type']
                    if innbytterPos == mids and not didNotPlay(spillerListe.iat[j,0]):
                        innbytterPos = teams.at[spillerListe.iat[j,0], 'element_type']
                        spillerListe.iat[i,0], spillerListe.iat[j,0] = spillerListe.iat[j,0], spillerListe.iat[i,0]
                        spillerListe.iat[i,1] = 1
                        countMid += 1
                        break

            if countAtt < minAtt:
                for j in range (len(spillerListe[12:15])):
                    innbytterPos = teams.at[spillerListe.iat[j,0], 'element_type']
                    if innbytterPos == atts and not didNotPlay(spillerListe.iat[j,0]):
                        innbytterPos = teams.at[spillerListe.iat[j,0], 'element_type']
                        spillerListe.iat[i,0], spillerListe.iat[j,0] = spillerListe.iat[j,0], spillerListe.iat[i,0]
                        spillerListe.iat[i,1] = 1
                        countAtt += 1
                        break

    return spillerListe[0:11][['element', 'multiplier']]


# Live bonus

def getBonusPoints(playerId):
    url2 = 'https://fantasy.premierleague.com/api/fixtures/?event=' + str(thisGw)
    r2 = requests.get(url2)
    json2 = r2.json()
    fixtures_df = pd.DataFrame(json2)
    stats_df_len = pd.DataFrame(fixtures_df['stats'].values.tolist())
    playerTeam = teams.at[playerId, 'team']
    
    bonus = 0
    
    for i in range(len(stats_df_len)):
        try:
            if fixtures_df.loc[(fixtures_df.team_a == playerTeam)].iat[0,6] < 60 or fixtures_df.loc[(fixtures_df.team_h == playerTeam)].iat[0,6] < 60:
                break
        except:
            pass
            
        try:
            
            if playerTeam == fixtures_df.at[i, 'team_a'] or playerTeam == fixtures_df.at[i, 'team_h']:
                stats_df = pd.DataFrame(fixtures_df['stats'].iloc[i]) # <- iloc[i]

                stats_a = pd.DataFrame(stats_df.loc[9,'a'])
                stats_h = pd.DataFrame(stats_df.loc[9,'h'])

                samlet = stats_h.append(stats_a)
                sort = samlet.sort_values(by=['value'], ascending=False)
                ferdig = sort.reset_index(drop=True)
            
                bps = ferdig[0:6]
            
                if bps.iat[0,0] == bps.iat[1,0] and (playerId == bps.iat[0,1] or playerId == bps.iat[1,1]):
                    bonus = 3
                    break
                if bps.iat[1,1] == bps.iat[2,0] and (playerId == bps.iat[1,1] or playerId == bps.iat[2,1]):
                    bonus = 2
                    break
                if bps.iat[2,1] == bps.iat[3,0] and (playerId == bps.iat[2,1] or playerId == bps.iat[3,1]):
                    bonus = 1
                    break
                if playerId == bps.iat[0,1]:
                    bonus = 3
                    break
                if playerId == bps.iat[1,1]:
                    bonus = 2
                    break
                if playerId == bps.iat[2,1]:
                    bonus = 1
                    break
        except:
            pass
    return bonus

def getLiveBonusList(teamId):
    picks = getAutoSubs(teamId)
    bonusPoeng = []
    
    for ids in picks['element']:
        bonusPoeng.append(getBonusPoints(ids))

    return bonusPoeng



def getTeamList():
    url2 = 'https://fantasy.premierleague.com/api/leagues-classic/627607/standings/'
    r2 = requests.get(url2)
    json2 = r2.json()
    standings_df = pd.DataFrame(json2['standings'])
    league_df = pd.DataFrame(standings_df['results'].values.tolist())
    return league_df ['entry']

teamsList = getTeamList()

def getAllPlayerList():
    url = 'https://fantasy.premierleague.com/api/event/' + str(thisGw) + '/live/'
    r = requests.get(url)
    json = r.json()
    liveElements_df = pd.DataFrame(json['elements'])
    liveId = liveElements_df['id']
    stats_df = pd.DataFrame(liveElements_df['stats'].values.tolist())
    liveTotPoints_df = pd.DataFrame(stats_df[['total_points', 'bonus']])
    liveTotPoints_df.insert(0,'id', liveId, True)
    return liveTotPoints_df

liveTotPoints = getAllPlayerList()



def getLivePlayerPoints(teamId):
    slim_picks = getAutoSubs(teamId)

    slim_picks['live_bonus'] = getLiveBonusList(teamId)

    poeng = 0
    for i in range(len(slim_picks)):
        tempId = slim_picks.iat[i,0]
        poeng += (liveTotPoints.iat[tempId - 1, 1] + slim_picks.iat[i, 2] -
                  liveTotPoints.iat[tempId - 1, 2]) * slim_picks.iat[i, 1]

    return poeng

gws = gwStart()
gwe = gwEnd()

def getGwRoundPoints(teamId):
    url = 'https://fantasy.premierleague.com/api/entry/' + str(teamId) + '/history/'
    r = requests.get(url)
    json = r.json()
    teamPoints_df = pd.DataFrame(json['current'])
    
    livePlayerPoints = getLivePlayerPoints(teamId) - teamPoints_df['event_transfers_cost'][thisGw-1]
    
    liveRound = (teamPoints_df['points'][gws:(thisGw - 1)].sum() + livePlayerPoints - teamPoints_df['event_transfers_cost'][gws:gwe - 1].sum() )
    total = teamPoints_df.iat[(thisGw - 2), 2] + livePlayerPoints
    
    return [total, liveRound, livePlayerPoints]

def getTeamsPoints():
    tabell = []
    for team in teamsList:
        tabell.append(getGwRoundPoints(team))
    
    tabell_df = pd.DataFrame(tabell)
    ny_tabell = tabell_df.rename(columns={0: "Total", 1: "GW", 2: "GWLive"})
    return ny_tabell

def getTabell():
    url2 = 'https://fantasy.premierleague.com/api/leagues-classic/627607/standings/'
    r2 = requests.get(url2)
    json2 = r2.json()
    standings_df = pd.DataFrame(json2['standings'])
    league_df = pd.DataFrame(standings_df['results'].values.tolist())

    tabell = getTeamsPoints()
    
    tabell.insert(0, 'Navn', league_df[['player_name']], True)
    tabellSort = tabell.sort_values ('GW', ascending=False)
    tabellSort.insert(0, "#", range(1, len(tabell) + 1), True)
    tabellSort.columns = ['#', 'Navn', 'Totalt', gwHeader(), 'GW'+str(thisGw)]
    

    return tabellSort

# Rundevinnere
def getRoundPoints(slutter):
    starter = slutter - 5
    slutter = starter + 4

    url2 = 'https://fantasy.premierleague.com/api/leagues-classic/627607/standings/'
    r2 = requests.get(url2)
    json2 = r2.json()
    standings_df = pd.DataFrame(json2['standings'])
    league_df = pd.DataFrame(standings_df['results'].values.tolist())
    teamid_df = league_df [['entry', 'player_name']]

    result = []

    # Finner scoren til alle spillerne i parmeterintervallet
    for team in teamid_df ['entry']:
        url = 'https://fantasy.premierleague.com/api/entry/' + str(team) + '/history/'
        r = requests.get(url)
        json = r.json()
        teamPoints_df = pd.DataFrame(json['current'])
        result.append(teamPoints_df['points'][starter:slutter].sum() - teamPoints_df['event_transfers_cost'][starter:slutter].sum() )

    # Setter spiller og poeng i liste
    navn = teamid_df['player_name']
    totpoints = result
    poeng = 0
    spiller = ""
    for i in range (len(navn)):
        if totpoints[i] > poeng:
            poeng = totpoints[i]
            spiller = navn[i]

    return [spiller, poeng]

def getWinners():
    rundeStart = [5, 9, 13, 17, 21, 25, 29, 33, 37]
    rundevinnere = []
    for obj in rundeStart:
        if gwStarter == obj:
            rundevinnere.append(getRoundPoints(obj))
    result = pd.DataFrame(rundevinnere)
    result.insert(0,'Runde', range(1, len(result) + 1), True)
    result.columns = ['Runde', 'Vinner', 'Poeng']
    return result


app = Flask(__name__)
app.config["DEBUG"] = True
    
@app.route("/")
def index():
    tabell = getTabell()
    vinner = getWinners()
    result = render_template('main_page.html', tables=[tabell.to_html(classes='tabeller'), vinner.to_html(classes='vinnere')],
    titles = ['na', 'Furuligaen', 'Vinnere'])
    return result
