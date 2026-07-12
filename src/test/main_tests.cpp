// Copyright (c) 2009-2019 The Bitcoin Core developers
// Copyright (c) 2014-2019 The DigiByte Core developers
// Copyright (c) 2026 The EGA Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <chainparams.h>
#include <validation.h>
#include <amount.h>
#include <net.h>

#include <test/test_digibyte.h>

#include <boost/signals2/signal.hpp>
#include <boost/test/unit_test.hpp>

BOOST_FIXTURE_TEST_SUITE(main_tests, TestingSetup)

// EGA: Bitcoin-style subsidy scaled — 50,000 EGA, halve every 210,000 blocks.
// See docs/ega/params.md

BOOST_AUTO_TEST_CASE(ega_block_subsidy_schedule)
{
    const auto chainParams = CreateChainParams(CBaseChainParams::MAIN);
    const Consensus::Params& consensusParams = chainParams->GetConsensus();

    BOOST_CHECK_EQUAL(consensusParams.nSubsidyHalvingInterval, 210000);

    BOOST_CHECK_EQUAL(GetBlockSubsidy(0, consensusParams), 50000 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(209999, consensusParams), 50000 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(210000, consensusParams), 25000 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(419999, consensusParams), 25000 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(420000, consensusParams), 12500 * COIN);
    BOOST_CHECK_EQUAL(GetBlockSubsidy(210000 * 64, consensusParams), 0);

    // Integer halvings sum to just under 21e9 EGA (same as Bitcoin-style math).
    CAmount nSum = 0;
    for (int era = 0; era < 64; ++era) {
        CAmount nSubsidy = GetBlockSubsidy(era * 210000, consensusParams);
        nSum += nSubsidy * 210000;
        if (nSubsidy == 0)
            break;
    }
    BOOST_CHECK(nSum > 20000000000LL * COIN);
    BOOST_CHECK(nSum <= 21000000000LL * COIN);
}

BOOST_AUTO_TEST_CASE(ega_money_constants)
{
    BOOST_CHECK_EQUAL(COIN, 100000000);
    BOOST_CHECK_EQUAL(MAX_MONEY, 21000000000LL * COIN);
    BOOST_CHECK(MAX_MONEY > 0);
    BOOST_CHECK(MoneyRange(MAX_MONEY));
    BOOST_CHECK(!MoneyRange(MAX_MONEY + 1));
    BOOST_CHECK(!MoneyRange(CAmount(-1)));
}

BOOST_AUTO_TEST_CASE(ega_network_params_smoke)
{
    const auto main = CreateChainParams(CBaseChainParams::MAIN);
    BOOST_CHECK_EQUAL(main->GetConsensus().nPowTargetSpacing, 60);
    BOOST_CHECK_EQUAL(main->GetConsensus().multiAlgoTargetSpacing, 180);
    BOOST_CHECK_EQUAL(main->GetDefaultPort(), 20201);
    BOOST_CHECK_EQUAL(main->Bech32HRP(), "ega");
}

static bool ReturnFalse() { return false; }
static bool ReturnTrue() { return true; }

BOOST_AUTO_TEST_CASE(test_combiner_all)
{
    boost::signals2::signal<bool (), CombinerAll> sig;
    BOOST_CHECK(sig());
    sig.connect(&ReturnFalse);
    BOOST_CHECK(!sig());
    sig.connect(&ReturnTrue);
    BOOST_CHECK(!sig());
    sig.disconnect(&ReturnFalse);
    BOOST_CHECK(sig());
    sig.disconnect(&ReturnTrue);
    BOOST_CHECK(sig());
}
BOOST_AUTO_TEST_SUITE_END()
