#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Apr  7 08:04:42 2017

Script to calculate matrix of probability of making division series 
vs. the game number in a season and win percentage.

Game data is taken from the 1990 - 2016 game logs from
http://www.retrosheet.org/gamelogs/index.html 

@author: jakelarson
"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


#  Return dictionary of teams in division series for year range
def getPlayoffData(minYear, maxYear):
    playoffFile = '../data/playoffData/GLDV.TXT'
    fIndex = ['date', 'TM1', 'TM2']
    playoffData = pd.read_csv(playoffFile, names=fIndex, usecols=[0, 3, 6])

    # create season reference column
    seasonArr = np.zeros(len(playoffData['date']))
    for i in range(len(playoffData['date'])):
        seasonArr[i] = str(playoffData['date'][i])[0:4]
    playoffData['season'] = seasonArr

    teamsInDivisionSeries = dict.fromkeys(np.arange(minYear, maxYear+1))
    for seasons in teamsInDivisionSeries:
        seasonData = playoffData[playoffData['season'] == seasons]
        teamsIn = set(list(set(seasonData['TM1'])) +
                               list(set(seasonData['TM2'])))
        teamsInDivisionSeries[seasons] = teamsIn

    return teamsInDivisionSeries


# Plot game num, win pct, and division series probability
def plotProbMatrix(totDivArr, trueDivArr):
    winPctMatrix = totDivArr/trueDivArr
    winPctMatrix = np.ma.masked_invalid(winPctMatrix)
    plt.figure()
    plt.imshow(100 * winPctMatrix[:, 0:162], extent=[1, 162, 0, 1],
               interpolation='none', cmap=plt.cm.YlGnBu, aspect=100)
    plt.xlabel('Game number')
    plt.ylabel('Win Pct')
    plt.colorbar(label='Division Series Probability %',
                 fraction=0.03, pad=0.04)
    plt.title('Division series probability vs. game number and win pct')
    plt.savefig('../figures/1990_2016_playoffprob', dpi=350)


# dirData = Directory for game logs from http://www.retrosheet.org/gamelogs/index.html
def runStats():
    dirData = '../data/seasonData/'
    columnRefs = np.genfromtxt(dirData + 'columnNameRef.csv',
                               delimiter=',', dtype=str)

    playoffData = getPlayoffData(1990, 2017)
    yearOfInterest = np.arange(1990, 2017, 1)

    trueDivArr = np.zeros((15, 164))
    totDivArr = np.zeros((15, 164))
    winPctRef = np.linspace(1, 0, 15)

    for year in yearOfInterest:
        print(year)
        dataFile = 'gl_1990_2016/GL%s.TXT' % year
        data = pd.read_csv(dirData+dataFile, names=columnRefs,
                           usecols=['hmScore', 'visScore', 'hmTeam', 'visTeam',
                                            'hmGameNum', 'visGameNum'])

        # Get list of all team names for that season, create dict
        teamNames = set(data['hmTeam'])
        dataDict = dict.fromkeys(teamNames)

        for names in teamNames:
            dataDict[names] = {}
            dataDict[names]['win_pct'] = np.zeros((164))
            dataDict[names]['totWins'] = 0
            if names in playoffData[year]:
                dataDict[names]['divSeries'] = 1
            else:
                dataDict[names]['divSeries'] = 0

        # Compute win PCT vs. game of the year
        for index, row in data.iterrows():
            hmTeam = row['hmTeam']
            visTeam = row['visTeam']
            hmTeamGames = row['hmGameNum']
            visTeamGames = row['visGameNum']

            # If home team wins...
            if (row['hmScore'] > row['visScore']):
                winsHm = dataDict[hmTeam]['totWins'] + 1
                dataDict[hmTeam]['win_pct'][hmTeamGames] = winsHm / hmTeamGames
                dataDict[hmTeam]['totWins'] = winsHm
                prevWins = dataDict[visTeam]['totWins']
                dataDict[visTeam]['win_pct'][visTeamGames] = prevWins / visTeamGames

            # If vis team wins...
            elif (row['hmScore'] < row['visScore']):
                winsVis = dataDict[visTeam]['totWins'] + 1
                dataDict[visTeam]['win_pct'][visTeamGames] = winsVis / visTeamGames
                dataDict[visTeam]['totWins'] = winsVis
                prevWins = dataDict[hmTeam]['totWins']
                dataDict[hmTeam]['win_pct'][hmTeamGames] = prevWins / hmTeamGames

            # If tie...give both half win
            elif (row['hmScore'] == row['visScore']):
                winsHm = dataDict[hmTeam]['totWins'] + 0.5
                winsVis = dataDict[visTeam]['totWins'] + 0.5
                dataDict[hmTeam]['win_pct'][hmTeamGames] = winsHm / hmTeamGames
                dataDict[visTeam]['win_pct'][visTeamGames] = winsVis / visTeamGames
                dataDict[hmTeam]['totWins'] = winsHm
                dataDict[visTeam]['totWins'] = winsVis

            # find pct binning index
            hmPctIndx = np.argmin(np.abs(winPctRef -
                                         dataDict[hmTeam]['win_pct'][hmTeamGames]))
            visPctIndx = np.argmin(np.abs(winPctRef -
                                          dataDict[visTeam]['win_pct'][visTeamGames]))

            # Input playoff data
            if dataDict[hmTeam]['divSeries'] == 1:
                totDivArr[hmPctIndx, hmTeamGames - 1] += 1
                trueDivArr[hmPctIndx, hmTeamGames - 1] += 1
            else:
                trueDivArr[hmPctIndx, hmTeamGames] += 1
            if dataDict[visTeam]['divSeries'] == 1:
                totDivArr[visPctIndx, visTeamGames - 1] += 1
                trueDivArr[visPctIndx, visTeamGames - 1] += 1
            else:
                trueDivArr[visPctIndx, visTeamGames - 1] += 1

    return totDivArr, trueDivArr

# Run plotting
totDivArr, trueDivArr = runStats()
plotProbMatrix(totDivArr, trueDivArr)
