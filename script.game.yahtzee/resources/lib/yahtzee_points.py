#!/usr/bin/python
# -*- coding: utf-8 -*-
#
#     Copyright (C) 2018 Mark König (mark.koenig@kleiner-schelm.de)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#

def GetCalc(button, dice):
    val = 0

    if(button == 1):
        val = AddUpDice(1, dice)
    elif(button == 2):
        val = AddUpDice(2, dice)
    elif(button == 3):
        val = AddUpDice(3, dice)
    elif(button == 4):
        val = AddUpDice(4, dice)
    elif(button == 5):
        val = AddUpDice(5, dice)
    elif(button == 6):
        val = AddUpDice(6, dice)
    elif(button == 8):
        val = CalculateThreeOfAKind(dice)
    elif(button == 9):
        val = CalculateFourOfAKind(dice)
    elif(button == 10):
        val = CalculateFullHouse(dice)
    elif(button == 11):
        val = CalculateSmallStraight(dice)
    elif(button == 12):
        val = CalculateLargeStraight(dice)
    elif(button == 13):
        val = CalculateYahtzee(dice)
    elif(button == 14):
        val = AddUpChance(dice)

    return val

def AddUpDice(no, dice):
    val = 0

    for i in range(5):
        if(dice[i] == no):
            val = val + no;

    return val

def CalculateThreeOfAKind(dice):
    val = 0
    ThreeOfAKind = False

    for x in range(6):
        cnt = 0
        for i in range(5):
            if (dice[i] == (x + 1)):
                cnt = cnt + 1
            if (cnt > 2):
                ThreeOfAKind = True
                break

    if (ThreeOfAKind):
        for i in range(5):
            val = val + dice[i]

    return val

def CalculateFourOfAKind(dice):
    val = 0
    FourOfAKind = False

    for x in range(6):
        cnt = 0
        for i in range(5):
            if (dice[i] == (x + 1)):
                cnt = cnt + 1
            if (cnt > 3):
                FourOfAKind = True
                break

    if (FourOfAKind):
        for i in range(5):
            val = val + dice[i]

    return val

def CalculateFullHouse(dice):
    val = 0
    i = sorted(dice)

    if ((((i[0] == i[1]) and (i[1] == i[2])) and # Three of a Kind
       (i[3] == i[4]) and # Two of a Kind
       (i[2] != i[3])) or
       ((i[0] == i[1]) and # Two of a Kind
       ((i[2] == i[3]) and (i[3] == i[4])) and # Three of a Kind
       (i[1] != i[2]))):
        val = 25;

    return val

def CalculateSmallStraight(dice):
    val = 0
    i = sorted(dice)

    # Problem can arise hear, if there is more than one of the same number, so
    # we must move any doubles to the end

    for j in range(4):
        if (i[j] == i[j + 1]):
            temp = i[j]
            for k in range(j, 4):
                i[k] = i[k + 1]
            i[4] = temp

    if(((i[0] == 1) and (i[1] == 2) and (i[2] == 3) and (i[3] == 4)) or
        ((i[0] == 2) and (i[1] == 3) and (i[2] == 4) and (i[3] == 5)) or
        ((i[0] == 3) and (i[1] == 4) and (i[2] == 5) and (i[3] == 6)) or
        ((i[1] == 1) and (i[2] == 2) and (i[3] == 3) and (i[4] == 4)) or
        ((i[1] == 2) and (i[2] == 3) and (i[3] == 4) and (i[4] == 5)) or
        ((i[1] == 3) and (i[2] == 4) and (i[3] == 5) and (i[4] == 6))):
        val = 30

    return val

def CalculateLargeStraight(dice):
    val = 0
    i = sorted(dice)

    if (((i[0] == 1) and (i[1] == 2) and (i[2] == 3) and (i[3] == 4) and (i[4] == 5)) or
        ((i[0] == 2) and (i[1] == 3) and (i[2] == 4) and (i[3] == 5) and (i[4] == 6))):

        val = 40

    return val

def CalculateYahtzee(dice):

    for x in range(6):
        cnt = 0
        for i in range(5):
            if (dice[i] == (x + 1)):
                cnt = cnt + 1
            if (cnt > 4):
                return 50
    return 0

def AddUpChance(dice):
    val = 0

    for i in range(5):
        val = val + dice[i]

    return val
