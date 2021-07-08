#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Date    : Jul-08-21 16:27
# @Author  : Kan HUANG (kan.huang@connect.ust.hk)
# @RefLink : https://github.com/GarethCa/Py-tANS

from collections import Counter
from math import floor, ceil
import random
import numpy as np
import matplotlib.pyplot as plt


class tANS(object):
    def __init__(args):
        pass


def first1Index(val):
    # Return the Index of the First Non-Zero Bit.
    counter = 0
    while val > 1:
        counter += 1
        val = val >> 1
    return counter


def outputNbBits(state, nbBits):
    # Output NbBits to a BitStream
    mask = (1 << nbBits) - 1
    little = state & mask
    if nbBits > 0:
        string = "{:b}".format(little)
    else:
        return ""
    while len(string) < nbBits:
        string = "0" + string
    return string


def encodeSymbol(symbol, state, bitStream, symbolTT, codingTable):
    """
    Args:
        symbol:
        state:
        bitStream:
        symbolTT:
        codingTable:
    """
    # Encode a Symbol Using tANS, giving the current state, the symbol, and the bitstream and STT
    symbolTT = symbolTT[symbol]
    nbBitsOut = (state + symbolTT['deltaNbBits']) >> 16
    bitStream += outputNbBits(state, nbBitsOut)
    state = codingTable[(state >> nbBitsOut) + symbolTT['deltaFindState']]
    return state, bitStream


def bitsToState(bitStream, nbBits):
    # Convert Bits from Bitstream to the new State.
    bits = bitStream[-nbBits:]
    rest = int(bits, 2)
    if nbBits == len(bitStream):
        remaining = ""
        return rest, remaining
    remaining = bitStream[:-nbBits]
    return rest, remaining


def decodeSymbol(state, bitStream, stateT):
    # Return a Symbol + New State + Bitstream from the bitStream and State.
    symbol = stateT[state]['symbol']
    nbBits = stateT[state]['nbBits']
    rest, bitStream = bitsToState(bitStream, nbBits)
    state = stateT[state]['newX'] + rest
    return symbol, state, bitStream

#####
# Functions to Encode and Decode Streams of Data.
#####


def encode_data(input_, symbolTT, codingTable):
    bitStream = ""
    state, bitStream = encodeSymbol(input_[0], 0, "", symbolTT, codingTable)
    bitStream = ""
    for char in input_:
        state, bitStream = encodeSymbol(
            char, state, bitStream, symbolTT, codingTable)
    # Includes Current Bit
    bitStream += outputNbBits(state - TABLE_SIZE, TABLE_LOG)
    return bitStream


def decode_data(bitStream, decodeTable):
    output = []
    state, bitStream = bitsToState(bitStream, TABLE_LOG)
    while len(bitStream) > 0:
        symbol, state, bitStream = decodeSymbol(state, bitStream, decodeTable)
        output = [symbol] + output
    return output


def split(string):
    # Split an Input String into a list of Symbols
    return [char for char in string]


TABLE_LOG = 5
TABLE_SIZE = 1 << TABLE_LOG


def main():

    # Define how often a symbol is seen, total should equal the table size.
    symbol_occurrences = {"0": 10, "1": 10, "2": 12}

    # Define the Initial Positions of States in StateList.
    symbol_list = [symbol for symbol,
                   occcurences in symbol_occurrences.items()]
    cumulative = [0 for _ in range(len(symbol_list)+2)]
    for u in range(1, len(symbol_occurrences.items()) + 1):
        cumulative[u] = cumulative[u - 1] + \
            list(symbol_occurrences.items())[u-1][1]
    cumulative[-1] = TABLE_SIZE + 1

    # Spread Symbols to Create the States Table
    highThresh = TABLE_SIZE - 1
    stateTable = [0 for _ in range(TABLE_SIZE)]
    tableMask = TABLE_SIZE - 1
    step = ((TABLE_SIZE >> 1) + (TABLE_SIZE >> 3) + 3)
    pos = 0
    for symbol, occurrences in symbol_occurrences.items():
        for i in range(occurrences):
            stateTable[pos] = symbol
            pos = (pos + step) & tableMask
            while pos > highThresh:
                position = (pos + step) & tableMask
    assert(pos == 0)
    print(stateTable)

    # Build Coding Table from State Table
    outputBits = [0 for _ in range(TABLE_SIZE)]
    codingTable = [0 for _ in range(TABLE_SIZE)]
    cumulative_cp = cumulative.copy()
    for i in range(TABLE_SIZE):
        s = stateTable[i]
        index = symbol_list.index(s)
        codingTable[cumulative_cp[index]] = TABLE_SIZE + i
        cumulative_cp[index] += 1
        outputBits[i] = TABLE_LOG - first1Index(TABLE_SIZE + i)

    #####
    # Create the Symbol Transformation Table
    #####
    total = 0
    symbolTT = {}
    for symbol, occurrences in symbol_occurrences.items():
        symbolTT[symbol] = {}
        if occurrences == 1:
            symbolTT[symbol]['deltaNbBits'] = (
                TABLE_LOG << 16) - (1 << TABLE_LOG)
            symbolTT[symbol]['deltaFindState'] = total - 1
        elif occurrences > 0:
            maxBitsOut = TABLE_LOG - first1Index(occurrences - 1)
            minStatePlus = occurrences << maxBitsOut
            symbolTT[symbol]['deltaNbBits'] = (maxBitsOut << 16) - minStatePlus
            symbolTT[symbol]['deltaFindState'] = total - occurrences
            total += occurrences
    print(symbolTT)

    # Generate a Decoding Table
    decodeTable = [{} for _ in range(TABLE_SIZE)]
    nextt = list(symbol_occurrences.items())
    for i in range(TABLE_SIZE):
        t = {}
        t['symbol'] = stateTable[i]
        index = symbol_list.index(t['symbol'])
        x = nextt[index][1]
        nextt[index] = (nextt[index][0], nextt[index][1] + 1)
        t['nbBits'] = TABLE_LOG - first1Index(x)
        t['newX'] = (x << t['nbBits']) - TABLE_SIZE
        decodeTable[i] = t

    # Test Encoding
    input_ = "1102010120"
    bitStream = encode_data(input_, symbolTT, codingTable)

    # Test Decoding
    output = decode_data(bitStream, decodeTable)

    # Assert that input and Output are the same
    print(split(input_), " = input")
    print(bitStream, " = bitStream")
    print(output, " = output")
    assert(split(input_) == output)


if __name__ == "__main__":
    main()
