// Copyright (c) 2010 Satoshi Nakamoto
// Copyright (c) 2009-2018 The DigiByte Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include "arith_uint256.h"
#include <chainparams.h>
#include <consensus/merkle.h>
#include <pow.h>
#include <primitives/block.h>

#include <tinyformat.h>
#include <util.h>
#include <utilstrencodings.h>

#include <assert.h>

#include <chainparamsseeds.h>

static CBlock CreateGenesisBlock(const char* pszTimestamp, const CScript& genesisOutputScript, uint32_t nTime, uint32_t nNonce, uint32_t nBits, int32_t nVersion, const CAmount& genesisReward)
{
    CMutableTransaction txNew;
    txNew.nVersion = 1;
    txNew.vin.resize(1);
    txNew.vout.resize(1);
    txNew.vin[0].scriptSig = CScript() << 486604799 << CScriptNum(4) << std::vector<unsigned char>((const unsigned char*)pszTimestamp, (const unsigned char*)pszTimestamp + strlen(pszTimestamp));
    txNew.vout[0].nValue = genesisReward;  // EGA: use passed reward (0 for fair launch)
    txNew.vout[0].scriptPubKey = CScript() << 0x0 << OP_CHECKSIG;

    CBlock genesis;
    genesis.nTime    = nTime;
    genesis.nBits    = nBits;
    genesis.nNonce   = nNonce;
    genesis.nVersion = nVersion;
    genesis.vtx.push_back(MakeTransactionRef(std::move(txNew)));
    genesis.hashPrevBlock.SetNull();
    genesis.hashMerkleRoot = BlockMerkleRoot(genesis);
    return genesis;
}

/**
 * EGA genesis: 0 premine, RandomX algo bits in nVersion, real PoW checked via GetPoWAlgoHash.
 * Mined with src/ega_mine_genesis (Phase 4). See docs/ega/phase-4-plan.md
 */
static CBlock CreateGenesisBlock(const char* pszTimestamp, uint32_t nTime, uint32_t nNonce, uint32_t nBits, int32_t nVersion, const CAmount& genesisReward)
{
    const CScript genesisOutputScript = CScript() << 0x0 << OP_CHECKSIG;
    return CreateGenesisBlock(pszTimestamp, genesisOutputScript, nTime, nNonce, nBits, nVersion, genesisReward);
}

void CChainParams::UpdateVersionBitsParameters(Consensus::DeploymentPos d, int64_t nStartTime, int64_t nTimeout)
{
    consensus.vDeployments[d].nStartTime = nStartTime;
    consensus.vDeployments[d].nTimeout = nTimeout;
}

/**
 * Main network
 */
/**
 * What makes a good checkpoint block?
 * + Is surrounded by blocks with reasonable timestamps
 *   (no blocks before with a timestamp after, none after with
 *    timestamp before)
 * + Contains no strange transactions
 */

class CMainParams : public CChainParams {
public:
    CMainParams() {
        strNetworkID = "main";
        // EGA: 50,000 EGA/block, halve every 210,000 blocks → ~21B total. See docs/ega/params.md
        consensus.nSubsidyHalvingInterval = 210000;
        consensus.BIP16Exception = uint256S("0x0");
        consensus.BIP34Height = 0;  // EGA: reset for new chain
        consensus.BIP34Hash = uint256S("0x0");
        consensus.BIP65Height = 0;
        consensus.BIP66Height = 0;

        // Initial powLimit: top 12 bits zero (~1/4096). Open enough for fair-launch mining;
        // MultiShield tightens from real hashrate. Must match genesis nBits compact form.
        consensus.powLimit = ArithToUint256(~arith_uint256(0) >> 12);
        consensus.initialTarget[ALGO_RANDOMX] = consensus.powLimit;
        consensus.initialTarget[ALGO_VERTHASH] = consensus.powLimit;
        consensus.initialTarget[ALGO_YESPOWER_EGA] = consensus.powLimit;
        consensus.nPowTargetTimespan = 14 * 24 * 60 * 60; // two weeks (legacy interval math)
        consensus.nPowTargetSpacing = 60;  // EGA: 1 minute blocks (overall)

        /** EGA Difficulty & Block Target (docs/ega/design.md)
        - Triple PoW (Phase 3): RandomX + Verthash + YespowerEGA
        - 60 second blocks overall; MultiShield per-algo spacing 180s (3 × 60)
        - 21B max supply, 50,000 EGA/block, halving every 210,000 blocks
        - MultiShield V4-style difficulty from height 0
        **/

        consensus.nTargetTimespan =  14 * 24 * 60 * 60; // 2 weeks
        consensus.nTargetSpacing = 60; // EGA: 1 minute
        consensus.nInterval = consensus.nTargetTimespan / consensus.nTargetSpacing;
        consensus.nDiffChangeTarget = 0; // EGA: MultiShield path from genesis (no old DigiShield ladder)

        // Old DGB reward periods unused — EGA uses simple halving in GetBlockSubsidy
        consensus.patchBlockRewardDuration = 0;
        consensus.patchBlockRewardDuration2 = 0;
        consensus.nTargetTimespanRe = 1*60; // 60 Seconds
        consensus.nTargetSpacingRe = 60; // EGA: 1 min
        consensus.nIntervalRe = consensus.nTargetTimespanRe / consensus.nTargetSpacingRe; // 1 block

        consensus.nAveragingInterval = 10; // 10 blocks
        // MultiShield: per-algo target ≈ NUM_ALGOS(3) × block time(60s)
        consensus.multiAlgoTargetSpacing = 180;
        consensus.multiAlgoTargetSpacingV4 = 180;
        consensus.nAveragingTargetTimespan = consensus.nAveragingInterval * consensus.multiAlgoTargetSpacing;
        consensus.nAveragingTargetTimespanV4 = consensus.nAveragingInterval * consensus.multiAlgoTargetSpacingV4;

        consensus.nMaxAdjustDown = 40; // 40% adjustment down
        consensus.nMaxAdjustUp = 20; // 20% adjustment up
        consensus.nMaxAdjustDownV3 = 16; // 16% adjustment down
        consensus.nMaxAdjustUpV3 = 8; // 8% adjustment up
        consensus.nMaxAdjustDownV4 = 16;
        consensus.nMaxAdjustUpV4 = 8;

        consensus.nMinActualTimespan = consensus.nAveragingTargetTimespan * (100 - consensus.nMaxAdjustUp) / 100;
        consensus.nMaxActualTimespan = consensus.nAveragingTargetTimespan * (100 + consensus.nMaxAdjustDown) / 100;
        consensus.nMinActualTimespanV3 = consensus.nAveragingTargetTimespan * (100 - consensus.nMaxAdjustUpV3) / 100;
        consensus.nMaxActualTimespanV3 = consensus.nAveragingTargetTimespan * (100 + consensus.nMaxAdjustDownV3) / 100;
        consensus.nMinActualTimespanV4 = consensus.nAveragingTargetTimespanV4 * (100 - consensus.nMaxAdjustUpV4) / 100;
        consensus.nMaxActualTimespanV4 = consensus.nAveragingTargetTimespanV4 * (100 + consensus.nMaxAdjustDownV4) / 100;

        consensus.nLocalTargetAdjustment = 4; //target adjustment per algo
        consensus.nLocalDifficultyAdjustment = 4; //difficulty adjustment per algo


        // EGA: simplified fork heights (many old DGB HF targets disabled for new chain)
        consensus.multiAlgoDiffChangeTarget = 0;
        consensus.alwaysUpdateDiffChangeTarget = 0;
        consensus.workComputationChangeTarget = 0;
        consensus.algoSwapChangeTarget = 0;

        consensus.fPowAllowMinDifficultyBlocks = false;
        consensus.fPowNoRetargeting = false;
        consensus.nRuleChangeActivationThreshold = 28224; // 28224 - 70% of 40320
        consensus.nMinerConfirmationWindow = 10080; // EGA: ~1 week at 60s blocks (7*24*60)
        consensus.fRbfEnabled = false;

        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].bit = 27; //Add VERSIONBITS_NUM_BITS_TO_SKIP (12)
        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nStartTime = 1199145601; // January 1, 2008
        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nTimeout = 1230767999; // December 31, 2008

        // Fresh EGA chain: standard soft forks active from genesis (no DigiByte BIP9 schedule).
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].bit = 12;
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].bit = 13;
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        consensus.vDeployments[Consensus::DEPLOYMENT_NVERSIONBIPS].bit = 14;
        consensus.vDeployments[Consensus::DEPLOYMENT_NVERSIONBIPS].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_NVERSIONBIPS].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        // Legacy DigiByte algo-reservation / Odo deployments: not used on EGA (triple PoW from genesis in Phase 3).
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].bit = 12;
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].bit = 6;
        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        consensus.nOdoShapechangeInterval = 10*24*60*60; // retained for unused Odo code paths

        // Fresh chain: no assumed work or skip-validation tip.
        consensus.nMinimumChainWork = uint256S("0x00");
        consensus.defaultAssumeValid = uint256S("0x00");

        /**
         * EGA message start — unique from DigiByte/Bitcoin so networks cannot cross-talk.
         * Bytes spell E G A + network id.
         */
        pchMessageStart[0] = 0xe4;
        pchMessageStart[1] = 0x47;
        pchMessageStart[2] = 0x41;
        pchMessageStart[3] = 0x01;  // main
        nDefaultPort = 20201;  // EGA main P2P (RPC 20202 — chainparamsbase)
        nPruneAfterHeight = 100000;

        // EGA main genesis (Phase 4 freeze). RandomX, 0 premine. See docs/ega/phase-4-plan.md
        genesis = CreateGenesisBlock(
            "EGA fair launch: equality of opportunity, not outcome — anyone may mine.",
            1751846400, 2816, 0x1f0fffff, BLOCK_VERSION_DEFAULT | BLOCK_VERSION_RANDOMX, 0);
        consensus.hashGenesisBlock = genesis.GetHash();
        assert(consensus.hashGenesisBlock == uint256S("943c83429a935b34fb988508440ec8702d217525865f3eea7076d64b4592eda5"));
        assert(genesis.hashMerkleRoot == uint256S("e30d15a8674c033ae2e00393f849b1d1bed85970b2aa7a5c6b843722020ddf01"));
        assert(CheckProofOfWork(genesis.GetPoWAlgoHash(consensus), genesis.nBits, consensus));

        // No DNS or fixed seeds at fair launch (docs/ega/design.md Phase 2).
        vSeeds.clear();
        vFixedSeeds.clear();

        // Address prefixes distinct from DigiByte (D=30) so keys/addresses are not interchangeable.
        // PUBKEY 33 → typical leading 'E' on base58check.
        base58Prefixes[PUBKEY_ADDRESS] = std::vector<unsigned char>(1, 33);
        base58Prefixes[SCRIPT_ADDRESS_OLD] = std::vector<unsigned char>(1, 5);
        base58Prefixes[SCRIPT_ADDRESS] = std::vector<unsigned char>(1, 92);
        base58Prefixes[SECRET_KEY] =     std::vector<unsigned char>(1, 176);
        base58Prefixes[SECRET_KEY_OLD] = std::vector<unsigned char>(1, 176);
        base58Prefixes[EXT_PUBLIC_KEY] = {0x04, 0x88, 0xB2, 0x1E};
        base58Prefixes[EXT_SECRET_KEY] = {0x04, 0x88, 0xAD, 0xE4};

        bech32_hrp = "ega";

        fDefaultConsistencyChecks = false;
        fRequireStandard = true;
        fMineBlocksOnDemand = false;

        // No historical DigiByte checkpoints on a new chain.
        checkpointData = {
            {
                {0, uint256S("943c83429a935b34fb988508440ec8702d217525865f3eea7076d64b4592eda5")},
            }
        };

        chainTxData = ChainTxData{
            0,
            0,
            0
        };

        /* disable fallback fee on mainnet */
        m_fallback_fee_enabled = false;
    }
};

/**
 * Testnet (v3)
 */
class CTestNetParams : public CChainParams {
public:
    CTestNetParams() {
        strNetworkID = "test";
        consensus.nSubsidyHalvingInterval = 210000; // same economy as main
        consensus.powLimit = ArithToUint256(~arith_uint256(0) >> 12);
        consensus.initialTarget[ALGO_RANDOMX] = consensus.powLimit;
        consensus.initialTarget[ALGO_VERTHASH] = consensus.powLimit;
        consensus.initialTarget[ALGO_YESPOWER_EGA] = consensus.powLimit;
        consensus.nPowTargetTimespan = 14 * 24 * 60 * 60; // two weeks
        consensus.nPowTargetSpacing = 60;  // EGA: 1 min blocks

        /** EGA testnet — same economic/timing foundation as main (docs/ega/params.md) */

        consensus.nTargetTimespan =  14 * 24 * 60 * 60; // 2 weeks
        consensus.nTargetSpacing = 60; // EGA: 1 minute
        consensus.nInterval = consensus.nTargetTimespan / consensus.nTargetSpacing;
        consensus.nDiffChangeTarget = 0; // MultiShield from genesis on EGA

        consensus.patchBlockRewardDuration = 0;
        consensus.patchBlockRewardDuration2 = 0;
        consensus.nTargetTimespanRe = 1*60; // 60 Seconds
        consensus.nTargetSpacingRe = 60; // EGA: 1 min
        consensus.nIntervalRe = consensus.nTargetTimespanRe / consensus.nTargetSpacingRe; // 1 block

        consensus.nAveragingInterval = 10; // 10 blocks
        consensus.multiAlgoTargetSpacing = 180; // 3 algos × 60s
        consensus.multiAlgoTargetSpacingV4 = 180;
        consensus.nAveragingTargetTimespan = consensus.nAveragingInterval * consensus.multiAlgoTargetSpacing;
        consensus.nAveragingTargetTimespanV4 = consensus.nAveragingInterval * consensus.multiAlgoTargetSpacingV4;

        consensus.nMaxAdjustDown = 40; // 40% adjustment down
        consensus.nMaxAdjustUp = 20; // 20% adjustment up
        consensus.nMaxAdjustDownV3 = 16; // 16% adjustment down
        consensus.nMaxAdjustUpV3 = 8; // 8% adjustment up
        consensus.nMaxAdjustDownV4 = 16;
        consensus.nMaxAdjustUpV4 = 8;

        consensus.nMinActualTimespan = consensus.nAveragingTargetTimespan * (100 - consensus.nMaxAdjustUp) / 100;
        consensus.nMaxActualTimespan = consensus.nAveragingTargetTimespan * (100 + consensus.nMaxAdjustDown) / 100;
        consensus.nMinActualTimespanV3 = consensus.nAveragingTargetTimespan * (100 - consensus.nMaxAdjustUpV3) / 100;
        consensus.nMaxActualTimespanV3 = consensus.nAveragingTargetTimespan * (100 + consensus.nMaxAdjustDownV3) / 100;
        consensus.nMinActualTimespanV4 = consensus.nAveragingTargetTimespanV4 * (100 - consensus.nMaxAdjustUpV4) / 100;
        consensus.nMaxActualTimespanV4 = consensus.nAveragingTargetTimespanV4 * (100 + consensus.nMaxAdjustDownV4) / 100;

        consensus.nLocalTargetAdjustment = 4; //target adjustment per algo
        consensus.nLocalDifficultyAdjustment = 4; //difficulty adjustment per algo


        // EGA: MultiShield / multi-algo active from height 0 (no DGB HF ladder)
        consensus.multiAlgoDiffChangeTarget = 0;
        consensus.alwaysUpdateDiffChangeTarget = 0;
        consensus.workComputationChangeTarget = 0;
        consensus.algoSwapChangeTarget = 0;

        consensus.fPowAllowMinDifficultyBlocks = true;
        consensus.fPowNoRetargeting = false;
        consensus.nRuleChangeActivationThreshold = 4032; // 4032 - 70% of 5760
        consensus.nMinerConfirmationWindow = 1440; // EGA test: ~1 day at 60s blocks
        consensus.fRbfEnabled = false;

        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].bit = 27; //Add VERSIONBITS_NUM_BITS_TO_SKIP (12)
        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nStartTime = 1199145601; // January 1, 2008
        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nTimeout = 1230767999; // December 31, 2008

        // Deployment of BIP68, BIP112, and BIP113.
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].bit = 12; //Add VERSIONBITS_NUM_BITS_TO_SKIP (12)
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        // Deployment of SegWit (BIP141, BIP143, and BIP147)
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].bit = 13; //Add VERSIONBITS_NUM_BITS_TO_SKIP (12)
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        // Deployment of BIP65, BIP66, and BIP34.
        consensus.vDeployments[Consensus::DEPLOYMENT_NVERSIONBIPS].bit = 14; //Add VERSIONBITS_NUM_BITS_TO_SKIP (12)
        consensus.vDeployments[Consensus::DEPLOYMENT_NVERSIONBIPS].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_NVERSIONBIPS].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        // Reservation of version bits for future algos
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].bit = 12;
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        // Deployment of Odo proof-of-work hardfork
        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].bit = 6;
        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].nStartTime = 1551398400; // 1 Mar, 2019
        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;

        consensus.nOdoShapechangeInterval = 1*24*60*60; // 1 day

        consensus.nMinimumChainWork = uint256S("0x00");
        consensus.defaultAssumeValid = uint256S("0x00");

        pchMessageStart[0] = 0xe4;
        pchMessageStart[1] = 0x47;
        pchMessageStart[2] = 0x41;
        pchMessageStart[3] = 0x02;  // EGA testnet
        nDefaultPort = 20203;  // EGA test P2P (RPC 20204)
        nPruneAfterHeight = 1000;

        genesis = CreateGenesisBlock(
            "EGA testnet: RandomX + Verthash + YespowerEGA MultiShield",
            1751846401, 2551, 0x1f0fffff, BLOCK_VERSION_DEFAULT | BLOCK_VERSION_RANDOMX, 0);
        consensus.hashGenesisBlock = genesis.GetHash();
        assert(consensus.hashGenesisBlock == uint256S("86ec8743951d8dcfcc7c6aad05c8a4365108f96075bf4c995dfbca98ffde1c98"));
        assert(genesis.hashMerkleRoot == uint256S("6b33d07186b851c3a2e750d2c2d9846be06bfdc18df4cf827d742b0d9c129501"));
        assert(CheckProofOfWork(genesis.GetPoWAlgoHash(consensus), genesis.nBits, consensus));

        vSeeds.clear();
        vFixedSeeds.clear();

        // Testnet address space distinct from main and DigiByte testnet.
        base58Prefixes[PUBKEY_ADDRESS] = std::vector<unsigned char>(1, 111); // typical 'm'/'n' style test
        base58Prefixes[SCRIPT_ADDRESS] = std::vector<unsigned char>(1, 196);
        base58Prefixes[SECRET_KEY] =     std::vector<unsigned char>(1, 239);
        base58Prefixes[EXT_PUBLIC_KEY] = {0x04, 0x35, 0x87, 0xCF};
        base58Prefixes[EXT_SECRET_KEY] = {0x04, 0x35, 0x83, 0x94};

        bech32_hrp = "tega";

        fDefaultConsistencyChecks = false;
        fRequireStandard = false;
        fMineBlocksOnDemand = false;

        checkpointData = {
            {
                {0, uint256S("86ec8743951d8dcfcc7c6aad05c8a4365108f96075bf4c995dfbca98ffde1c98")},
            }
        };

        chainTxData = ChainTxData{
            0,
            0,
            0
        };

        m_fallback_fee_enabled = true;
    }
};

/**
 * Regression test
 */
class CRegTestParams : public CChainParams {
public:
    CRegTestParams() {
        strNetworkID = "regtest";
        consensus.nSubsidyHalvingInterval = 150; // short interval for regtest (economy shape tested on main params)
        consensus.powLimit = uint256S("7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
        consensus.fPowAllowMinDifficultyBlocks = true;
        consensus.nPowTargetTimespan = 14 * 24 * 60 * 60; // two weeks
        consensus.nPowTargetSpacing = 60;  // EGA: 1 min blocks (same foundation as main)
        consensus.nTargetTimespan =  14 * 24 * 60 * 60; // 2 weeks
        consensus.nTargetSpacing = 60; // EGA: 1 minute
        consensus.nInterval = consensus.nTargetTimespan / consensus.nTargetSpacing;
        consensus.nDiffChangeTarget = 0;

        consensus.patchBlockRewardDuration = 0;
        consensus.patchBlockRewardDuration2 = 0;
        consensus.nTargetTimespanRe = 1*60; // 60 Seconds
        consensus.nTargetSpacingRe = 60; // EGA: 1 min
        consensus.nIntervalRe = consensus.nTargetTimespanRe / consensus.nTargetSpacingRe; // 1 block

        consensus.nAveragingInterval = 10; // 10 blocks
        consensus.multiAlgoTargetSpacing = 180; // 3 algos × 60s
        consensus.multiAlgoTargetSpacingV4 = 180;
        consensus.nAveragingTargetTimespan = consensus.nAveragingInterval * consensus.multiAlgoTargetSpacing;
        consensus.nAveragingTargetTimespanV4 = consensus.nAveragingInterval * consensus.multiAlgoTargetSpacingV4;

        consensus.nMaxAdjustDown = 40; // 40% adjustment down
        consensus.nMaxAdjustUp = 20; // 20% adjustment up
        consensus.nMaxAdjustDownV3 = 16; // 16% adjustment down
        consensus.nMaxAdjustUpV3 = 8; // 8% adjustment up
        consensus.nMaxAdjustDownV4 = 16;
        consensus.nMaxAdjustUpV4 = 8;

        consensus.nMinActualTimespan = consensus.nAveragingTargetTimespan * (100 - consensus.nMaxAdjustUp) / 100;
        consensus.nMaxActualTimespan = consensus.nAveragingTargetTimespan * (100 + consensus.nMaxAdjustDown) / 100;
        consensus.nMinActualTimespanV3 = consensus.nAveragingTargetTimespan * (100 - consensus.nMaxAdjustUpV3) / 100;
        consensus.nMaxActualTimespanV3 = consensus.nAveragingTargetTimespan * (100 + consensus.nMaxAdjustDownV3) / 100;
        consensus.nMinActualTimespanV4 = consensus.nAveragingTargetTimespanV4 * (100 - consensus.nMaxAdjustUpV4) / 100;
        consensus.nMaxActualTimespanV4 = consensus.nAveragingTargetTimespanV4 * (100 + consensus.nMaxAdjustDownV4) / 100;

        consensus.nLocalTargetAdjustment = 4; //target adjustment per algo
        consensus.nLocalDifficultyAdjustment = 4; //difficulty adjustment per algo

        consensus.BIP65Height = 1351;
        consensus.BIP66Height = 1251;

        // EGA: MultiShield / multi-algo from height 0
        consensus.multiAlgoDiffChangeTarget = 0;
        consensus.alwaysUpdateDiffChangeTarget = 0;
        consensus.workComputationChangeTarget = 0;
        consensus.algoSwapChangeTarget = 0;
        consensus.nMinerConfirmationWindow = 1440; // regtest window (~1 day at 60s if used)

        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].bit = 28;
        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nStartTime = 0;
        consensus.vDeployments[Consensus::DEPLOYMENT_TESTDUMMY].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].bit = 0;
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].nStartTime = 0;
        consensus.vDeployments[Consensus::DEPLOYMENT_CSV].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].bit = 1;
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_SEGWIT].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].bit = 2;
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;
        consensus.vDeployments[Consensus::DEPLOYMENT_RESERVEALGO].nTimeout = Consensus::BIP9Deployment::NO_TIMEOUT;
        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].bit = 6;
        consensus.vDeployments[Consensus::DEPLOYMENT_ODO].nStartTime = Consensus::BIP9Deployment::ALWAYS_ACTIVE;

        consensus.nOdoShapechangeInterval = 60; // 1 minute

        consensus.nMinimumChainWork = uint256S("0x00");
        consensus.defaultAssumeValid = uint256S("0x00");

        pchMessageStart[0] = 0xe4;
        pchMessageStart[1] = 0x47;
        pchMessageStart[2] = 0x41;
        pchMessageStart[3] = 0x03;  // EGA regtest
        nDefaultPort = 20205;  // EGA regtest P2P (RPC 20206 — must differ from P2P)
        nPruneAfterHeight = 1000;

        genesis = CreateGenesisBlock(
            "EGA regtest",
            1751846402, 0, 0x207fffff, BLOCK_VERSION_DEFAULT | BLOCK_VERSION_RANDOMX, 0);
        consensus.hashGenesisBlock = genesis.GetHash();
        assert(consensus.hashGenesisBlock == uint256S("7db0bcedfac1596d0be2a5b42c4b88043c207f8f29bac2796fba10ea06ae5ac0"));
        assert(genesis.hashMerkleRoot == uint256S("492e199b683b7b542713244df27840e94dee345d02ac62c21c79b82b334c02b8"));
        assert(CheckProofOfWork(genesis.GetPoWAlgoHash(consensus), genesis.nBits, consensus));

        vFixedSeeds.clear();
        vSeeds.clear();

        fDefaultConsistencyChecks = true;
        fRequireStandard = false;
        fMineBlocksOnDemand = true;

        checkpointData = {
            {
                {0, uint256S("7db0bcedfac1596d0be2a5b42c4b88043c207f8f29bac2796fba10ea06ae5ac0")},
            }
        };

        chainTxData = ChainTxData{
            0,
            0,
            0
        };

        base58Prefixes[PUBKEY_ADDRESS] = std::vector<unsigned char>(1, 111);
        base58Prefixes[SCRIPT_ADDRESS] = std::vector<unsigned char>(1, 196);
        base58Prefixes[SECRET_KEY] =     std::vector<unsigned char>(1, 239);
        base58Prefixes[EXT_PUBLIC_KEY] = {0x04, 0x35, 0x87, 0xCF};
        base58Prefixes[EXT_SECRET_KEY] = {0x04, 0x35, 0x83, 0x94};

        bech32_hrp = "egart";
    }
};

static std::unique_ptr<CChainParams> globalChainParams;

const CChainParams &Params() {
    assert(globalChainParams);
    return *globalChainParams;
}

std::unique_ptr<CChainParams> CreateChainParams(const std::string& chain)
{
    if (chain == CBaseChainParams::MAIN)
        return std::unique_ptr<CChainParams>(new CMainParams());
    else if (chain == CBaseChainParams::TESTNET)
        return std::unique_ptr<CChainParams>(new CTestNetParams());
    else if (chain == CBaseChainParams::REGTEST)
        return std::unique_ptr<CChainParams>(new CRegTestParams());
    throw std::runtime_error(strprintf("%s: Unknown chain %s.", __func__, chain));
}

void SelectParams(const std::string& network)
{
    SelectBaseParams(network);
    globalChainParams = CreateChainParams(network);
}

void UpdateVersionBitsParameters(Consensus::DeploymentPos d, int64_t nStartTime, int64_t nTimeout)
{
    globalChainParams->UpdateVersionBitsParameters(d, nStartTime, nTimeout);
}
