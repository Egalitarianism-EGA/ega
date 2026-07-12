// Copyright (c) 2026 The EGA Core developers
// Distributed under the MIT software license.

#include <arith_uint256.h>
#include <chainparams.h>
#include <crypto/ega_pow.h>
#include <pow.h>
#include <primitives/block.h>
#include <uint256.h>

#include <test/test_digibyte.h>

#include <boost/test/unit_test.hpp>
#include <cstring>

BOOST_FIXTURE_TEST_SUITE(ega_pow_tests, BasicTestingSetup)

BOOST_AUTO_TEST_CASE(algo_names_and_versions)
{
    BOOST_CHECK_EQUAL(NUM_ALGOS, 3);
    BOOST_CHECK_EQUAL(GetAlgoName(ALGO_RANDOMX), "randomx");
    BOOST_CHECK_EQUAL(GetAlgoName(ALGO_VERTHASH), "verthash");
    BOOST_CHECK_EQUAL(GetAlgoName(ALGO_YESPOWER_EGA), "yespower-ega");

    BOOST_CHECK_EQUAL(GetAlgoByName("randomx", -1), ALGO_RANDOMX);
    BOOST_CHECK_EQUAL(GetAlgoByName("rx", -1), ALGO_RANDOMX);
    BOOST_CHECK_EQUAL(GetAlgoByName("verthash", -1), ALGO_VERTHASH);
    BOOST_CHECK_EQUAL(GetAlgoByName("yespower-ega", -1), ALGO_YESPOWER_EGA);
    BOOST_CHECK_EQUAL(GetAlgoByName("yespower", -1), ALGO_YESPOWER_EGA);
    BOOST_CHECK_EQUAL(GetAlgoByName("nope", 99), 99);

    BOOST_CHECK_EQUAL(GetVersionForAlgo(ALGO_RANDOMX), BLOCK_VERSION_RANDOMX);
    BOOST_CHECK_EQUAL(GetVersionForAlgo(ALGO_VERTHASH), BLOCK_VERSION_VERTHASH);
    BOOST_CHECK_EQUAL(GetVersionForAlgo(ALGO_YESPOWER_EGA), BLOCK_VERSION_YESPOWER_EGA);
}

BOOST_AUTO_TEST_CASE(pow_hashes_differ_by_algo)
{
    CBlockHeader header;
    header.nVersion = BLOCK_VERSION_DEFAULT | BLOCK_VERSION_RANDOMX;
    header.hashPrevBlock.SetNull();
    header.hashMerkleRoot.SetNull();
    header.nTime = 1751846400;
    header.nBits = 0x1f0fffff;
    header.nNonce = 1;

    const auto params = CreateChainParams(CBaseChainParams::MAIN)->GetConsensus();

    header.nVersion = BLOCK_VERSION_DEFAULT | BLOCK_VERSION_RANDOMX;
    uint256 h_rx = header.GetPoWAlgoHash(params);

    header.nVersion = BLOCK_VERSION_DEFAULT | BLOCK_VERSION_VERTHASH;
    uint256 h_vh = header.GetPoWAlgoHash(params);

    header.nVersion = BLOCK_VERSION_DEFAULT | BLOCK_VERSION_YESPOWER_EGA;
    uint256 h_yp = header.GetPoWAlgoHash(params);

    BOOST_CHECK(h_rx != h_vh);
    BOOST_CHECK(h_rx != h_yp);
    BOOST_CHECK(h_vh != h_yp);

    // Not the "invalid work" sentinel (~0)
    uint256 maxHash = ArithToUint256(~arith_uint256(0));
    BOOST_CHECK(h_rx != maxHash);
    BOOST_CHECK(h_vh != maxHash);
    BOOST_CHECK(h_yp != maxHash);
}

BOOST_AUTO_TEST_CASE(main_genesis_pow_valid)
{
    const auto chainParams = CreateChainParams(CBaseChainParams::MAIN);
    const CBlock& genesis = chainParams->GenesisBlock();
    const Consensus::Params& consensus = chainParams->GetConsensus();

    BOOST_CHECK(CheckProofOfWork(genesis.GetPoWAlgoHash(consensus), genesis.nBits, consensus));
    BOOST_CHECK_EQUAL(genesis.GetAlgo(), ALGO_RANDOMX);
}

BOOST_AUTO_TEST_SUITE_END()
