// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2016 The DigiByte Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#ifndef DIGIBYTE_AMOUNT_H
#define DIGIBYTE_AMOUNT_H

#include <stdint.h>

/** Amount in base units (can be negative) */
typedef int64_t CAmount;

/** 1 EGA = 100_000_000 base units (8 decimal places). See docs/ega/params.md */
static const CAmount COIN = 100000000;
static const CAmount CENT = 1000000;

/** No amount larger than this (in base units) is valid.
 *
 * This is a consensus-critical sanity check, not a statement of circulating
 * supply. EGA max supply is 21,000,000,000 EGA with 8 decimals.
 * Must fit in int64: 21e9 * 1e8 = 2.1e18 < 9.22e18.
 */
static const CAmount MAX_MONEY = 21000000000LL * COIN;
inline bool MoneyRange(const CAmount& nValue) { return (nValue >= 0 && nValue <= MAX_MONEY); }

#endif //  DIGIBYTE_AMOUNT_H
