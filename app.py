
# A very simple Flask Hello World app for you to get started with...
from flask import Flask, render_template
from numpy.lib.shape_base import split
import pandas as pd
import requests
from datetime import timedelta, datetime

app = Flask(__name__)
app.config["DEBUG"] = True

@app.route("/")
def index():
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
        gw = thisGw
        liste = [5, 9, 13, 17, 21, 25, 29, 33, 37]
        for obj in liste:
            if gw < obj:
                return obj - 4 
        else:
            return 37     

    # Minus 1 for å treffe index 0

    getGwStart1 = getGwStart()

    def gwEnd ():
        gw = getGwStart1
        if gw == 37 or gw == 38:
            return 38
        else:
            return gw + 3
    
    getGwEnd1 = gwEnd()

    # For header i tabell
    def gwHeader():
        return "GW " + str(getGwStart1) + " -> " + str(getGwEnd1)

    # Auto subs
    def getBootstrapTeams():
        url4 = 'https://fantasy.premierleague.com/api/bootstrap-static/'
        r4 = requests.get(url4)
        json = r4.json()
        gameweek_df = pd.DataFrame(json['elements'])
        teams = gameweek_df[['id', 'team', 'element_type']]
        teams.set_index('id', inplace = True)
        return teams

    teams = getBootstrapTeams()

    def getGwFixtures():
        url2 = 'https://fantasy.premierleague.com/api/fixtures/?event=' + str(thisGw)
        r2 = requests.get(url2)
        json2 = r2.json()
        fixtures_df = pd.DataFrame(json2)
        
        hfixtures = fixtures_df[['team_h', 'finished_provisional']]

        aFixtures = fixtures_df[['team_a', 'finished_provisional']]
        aFixtures.columns = ['team_h', 'finished_provisional']
        
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

    minutes = getMinutesPlayed()

    def didNotPlay(playerId):
        teamId = teams.at[playerId, 'team']
        return minutes.at[playerId, 'minutes'] == 0 and allFix.at[teamId, 'finished_provisional']

    def getAutoSubs(teamId):   
        url4 = 'https://fantasy.premierleague.com/api/entry/' + str(teamId) + '/event/' + str(thisGw) + '/picks/'
        r4 = requests.get(url4)
        json4 = r4.json()
        picks_df = pd.DataFrame(json4['picks'])

        spillerListeOrg = picks_df[['element', 'multiplier', 'is_captain', 'is_vice_captain']]
        
        spillerListe = spillerListeOrg.copy()

        minDef = 3
        minMid = 2
        minAtt = 1

        countGk = 0
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
                if spillerpos == gk:
                    countGk += 1
                if spillerpos == defs:
                    countDef += 1
                if spillerpos == mids:
                    countMid += 1
                if spillerpos == atts:
                    countAtt += 1

        for i in range(len(spillerListe[0:11])):
            if (countGk + countDef + countMid + countAtt) == 11:
                break
            
            starter = spillerListe.iat[i,0]
            spilteIkke = didNotPlay(starter)
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
                    countGk += 1
                else:
                    countGk += 1
                    
            # bytte fra benken
            if spillerpos != gk and spilteIkke:
                
                spillerListe.iat[i,1] = 0
                byttet = False

                for j in range (len(spillerListe[12:15])):
                    if didNotPlay(spillerListe[12:15].iat[j,0]):
                        continue
                    
                    innbytterPos = teams.at[spillerListe[12:15].iat[j,0], 'element_type']

                    if countDef >= minDef and countMid >= minMid and countAtt >= minAtt:
                        spillerListe.iat[i,0], spillerListe[12:15].iat[j,0] = spillerListe[12:15].iat[j,0], spillerListe.iat[i,0] 
                        spillerListe.iat[i,1] = 1

                        if innbytterPos == defs:
                            countDef += 1
                        if innbytterPos == mids:
                            countMid += 1
                        if innbytterPos == atts:
                            countAtt += 1
                        byttet = True
                        break           
                            
                    if countDef < minDef and innbytterPos == defs:
                        spillerListe.iat[i,0], spillerListe[12:15].iat[j,0] = spillerListe[12:15].iat[j,0], spillerListe.iat[i,0]
                        spillerListe.iat[i,1] = 1
                        countDef += 1
                        byttet = True
                        break

                    if countMid < minMid and innbytterPos == mids:
                        spillerListe.iat[i,0], spillerListe[12:15].iat[j,0] = spillerListe[12:15].iat[j,0], spillerListe.iat[i,0]
                        spillerListe.iat[i,1] = 1
                        countMid += 1
                        byttet = True
                        break

                    if countAtt < minAtt and innbytterPos == atts:
                        spillerListe.iat[i,0], spillerListe[12:15].iat[j,0] = spillerListe[12:15].iat[j,0], spillerListe.iat[i,0]
                        spillerListe.iat[i,1] = 1
                        countAtt += 1
                        byttet = True
                        break
                    
                if byttet == False:
                    if spillerpos == defs:
                        countDef += 1
                    if spillerpos == mids:
                        countMid += 1
                    if spillerpos == atts:
                        countAtt += 1
                    
        return spillerListe[0:11][['element', 'multiplier']]

    # Live bonus

    def getBonusLists():
        liste = pd.DataFrame()
        url = 'https://fantasy.premierleague.com/api/fixtures/?event=' + str(thisGw)
        r = requests.get(url)
        json = r.json()
        fixtures_df = pd.DataFrame(json)
        for i in range (len(fixtures_df)):
            try:
                stats_df = pd.DataFrame(fixtures_df['stats'].iloc[i])
                stats_a = pd.DataFrame(stats_df.loc[9,'a'])
                stats_h = pd.DataFrame(stats_df.loc[9,'h'])
                samlet = stats_a.append(stats_h)
                sort = samlet.sort_values(by=['value'], ascending=False)
                ferdig = sort.reset_index(drop=True)
                bps = ferdig[0:6].copy()
                bps['bonus'] = 0
            
                # Delt første
                if bps.iat[0,0] == bps.iat[1,0]:
                    bps.at[0,'bonus'] = 3
                    bps.at[1,'bonus'] = 3
                    bps.at[2,'bonus'] = 1
                    liste = liste.append(bps, ignore_index = True, sort = False)
                # Delt andreplass   
                elif bps.iat[1,0] == bps.iat[2,0]:
                    bps.at[0,'bonus'] = 3
                    bps.at[1,'bonus'] = 2
                    bps.at[2,'bonus'] = 2
                # Delt tredje
                elif bps.iat[2,0] == bps.iat[3,0]:
                    bps.at[0,'bonus'] = 3
                    bps.at[1,'bonus'] = 2
                    bps.at[2,'bonus'] = 1
                    bps.at[3,'bonus'] = 1
                    liste = liste.append(bps, ignore_index = True, sort = False)
                else:
                    bps.at[0,'bonus'] = 3
                    bps.at[1,'bonus'] = 2
                    bps.at[2,'bonus'] = 1
                    liste = liste.append(bps, ignore_index = True, sort = False)
            except:
                pass
        return liste.set_index('element', inplace=False)['bonus']
    
    bonuspoints = getBonusLists()

    def getLiveBonusList(teamId):
        picks = getAutoSubs(teamId)
        bonusPoeng = []
        for ids in picks['element']:
            try:
                bonusPoeng.append(bonuspoints.at[ids])
            except:
                bonusPoeng.append(0)
        return bonusPoeng

    def getTeamList():
        url2 = 'https://fantasy.premierleague.com/api/leagues-classic/627607/standings/'
        r2 = requests.get(url2)
        json2 = r2.json()
        standings_df = pd.DataFrame(json2['standings'])
        league_df = pd.DataFrame(standings_df['results'].values.tolist())
        return league_df [['entry', 'player_name']]


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

    gws = getGwStart1
    gwe = getGwEnd1

    def getGwRoundPoints(teamId):
        url = 'https://fantasy.premierleague.com/api/entry/' + str(teamId) + '/history/'
        r = requests.get(url)
        json = r.json()
        teamPoints_df = pd.DataFrame(json['current'])
        
        livePlayerPoints = getLivePlayerPoints(teamId) 
        
        livePlayerPoints_trans = livePlayerPoints - teamPoints_df['event_transfers_cost'][thisGw-1]
        
        liveRound = (teamPoints_df['points'][gws:(thisGw - 1)].sum() + livePlayerPoints - teamPoints_df['event_transfers_cost'][gws-1:gwe].sum() )
        
        total = teamPoints_df.iat[(thisGw - 2), 2] + livePlayerPoints_trans
        
        return [total, livePlayerPoints_trans, liveRound]

    teamsList = getTeamList()
    
    def getTeamsPoints():
        tabell = []
        for team in teamsList['entry']:
            tabell.append(getGwRoundPoints(team))
        
        tabell_df = pd.DataFrame(tabell)
        ny_tabell = tabell_df.rename(columns={0: "Total", 1: "GWLive", 2: "Round"})
        return ny_tabell

    def getTabell():
        url2 = 'https://fantasy.premierleague.com/api/leagues-classic/627607/standings/'
        r2 = requests.get(url2)
        json2 = r2.json()
        standings_df = pd.DataFrame(json2['standings'])
        league_df = pd.DataFrame(standings_df['results'].values.tolist())

        tabell = getTeamsPoints()
        
        tabell.insert(0, 'Navn', league_df[['player_name']], True)
        tabellSort = tabell.sort_values ('Round', ascending=False)
        tabellSort.insert(0, "#", range(1, len(tabell) + 1), True)
        tabellSort.columns = ['#', 'Navn', 'Tot', 'GW'+str(thisGw), gwHeader()]
        

        return tabellSort

    # Rundevinnere
    def getRoundPoints(slutter):
        starter = slutter - 5
        slutter = starter + 4

        result = []
        navn = []
        # Finner scoren til alle spillerne i parmeterintervallet
        
        for i in range (len(teamsList)):
            url = 'https://fantasy.premierleague.com/api/entry/' + str(teamsList.iat[i,0]) + '/history/'
            r = requests.get(url)
            json = r.json()
            teamPoints_df = pd.DataFrame(json['current'])
            result.append(teamPoints_df['points'][starter:slutter].sum() - 
                        teamPoints_df['event_transfers_cost'][starter:slutter].sum())
            navn.append(teamsList.iat[i,1])
        
        samlet = pd.DataFrame(result, navn)
        samlet.reset_index(inplace = True)
        maxClm = samlet.loc[samlet[0].argmax()]
        
        return maxClm

    def getWinners():
        nyRunde = [5, 9, 13, 17, 21, 25, 29, 33, 37]
        rundevinnere = []
        for obj in nyRunde:
            if getGwStart1 < obj:
                break
            if getGwStart1 >= obj:
                rundevinnere.append(getRoundPoints(obj))
                
        result = pd.DataFrame(rundevinnere)
        result.insert(0,'Runde', range(1, len(result) + 1), True)
        result.columns = ['Runde', 'Vinner', 'Poeng']
        return result

    result = render_template('main_page.html', tables=[getTabell().to_html(classes='tabeller'), getWinners().to_html(classes='vinnere')],
    titles = ['na', 'Furuligaen', 'Vinnere'])
    return result
