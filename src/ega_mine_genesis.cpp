// Copyright (c) 2026 The EGA Core developers
// One-shot genesis miner for Phase 4. Build: make -C src ega_mine_genesis
// Usage: ./ega_mine_genesis [main|test|regtest]

#include <arith_uint256.h>
#include <chainparams.h>
#include <consensus/merkle.h>
#include <crypto/ega_pow.h>
#include <primitives/block.h>
#include <primitives/transaction.h>
#include <script/script.h>
#include <utilstrencodings.h>
#include <uint256.h>
#include <version.h>

#include <cstdio>
#include <cstring>
#include <string>

static CBlock MakeGenesis(const char* pszTimestamp, uint32_t nTime, uint32_t nNonce,
                          uint32_t nBits, int32_t nVersion)
{
    CMutableTransaction txNew;
    txNew.nVersion = 1;
    txNew.vin.resize(1);
    txNew.vout.resize(1);
    txNew.vin[0].scriptSig = CScript() << 486604799 << CScriptNum(4)
        << std::vector<unsigned char>((const unsigned char*)pszTimestamp,
                                      (const unsigned char*)pszTimestamp + strlen(pszTimestamp));
    txNew.vout[0].nValue = 0; // fair launch
    txNew.vout[0].scriptPubKey = CScript() << 0x0 << OP_CHECKSIG;

    CBlock genesis;
    genesis.nTime = nTime;
    genesis.nBits = nBits;
    genesis.nNonce = nNonce;
    genesis.nVersion = nVersion;
    genesis.vtx.push_back(MakeTransactionRef(std::move(txNew)));
    genesis.hashPrevBlock.SetNull();
    genesis.hashMerkleRoot = BlockMerkleRoot(genesis);
    return genesis;
}

static void Mine(const char* name, const char* timestamp, uint32_t nTime, uint32_t nBits, int32_t nVersion)
{
    Consensus::Params dummy;
    CBlock genesis = MakeGenesis(timestamp, nTime, 0, nBits, nVersion);

    arith_uint256 hashTarget;
    bool fNegative, fOverflow;
    hashTarget.SetCompact(nBits, &fNegative, &fOverflow);
    if (fNegative || fOverflow || hashTarget == 0) {
        fprintf(stderr, "%s: bad nBits\n", name);
        return;
    }

    printf("Mining %s genesis (algo=%s, nBits=0x%08x, target=%s)...\n",
           name, GetAlgoName(genesis.GetAlgo()).c_str(), nBits,
           ArithToUint256(hashTarget).ToString().c_str());
    fflush(stdout);

    uint32_t report = 0;
    for (;;) {
        uint256 powHash = genesis.GetPoWAlgoHash(dummy);
        if (UintToArith256(powHash) <= hashTarget) {
            printf("\n=== %s GENESIS FOUND ===\n", name);
            printf("timestamp: %s\n", timestamp);
            printf("CreateGenesisBlock(%u, %u, 0x%08x, %d, 0);\n",
                   genesis.nTime, genesis.nNonce, genesis.nBits, genesis.nVersion);
            printf("hashGenesisBlock = %s\n", genesis.GetHash().ToString().c_str());
            printf("powHash          = %s\n", powHash.ToString().c_str());
            printf("merkleRoot       = %s\n", genesis.hashMerkleRoot.ToString().c_str());
            printf("assert(consensus.hashGenesisBlock == uint256S(\"%s\"));\n",
                   genesis.GetHash().ToString().c_str());
            printf("assert(genesis.hashMerkleRoot == uint256S(\"%s\"));\n",
                   genesis.hashMerkleRoot.ToString().c_str());
            printf("========================\n\n");
            fflush(stdout);
            return;
        }
        ++genesis.nNonce;
        if ((++report % 50) == 0) {
            printf("  %s nonce=%u pow=%s\n", name, genesis.nNonce, powHash.ToString().c_str());
            fflush(stdout);
        }
        if (genesis.nNonce == 0) {
            fprintf(stderr, "%s: nonce wrapped\n", name);
            return;
        }
    }
}

int main(int argc, char** argv)
{
    // EGA genesis uses RandomX (version field algo bits = 0) + BLOCK_VERSION_DEFAULT
    const int32_t nVersion = BLOCK_VERSION_DEFAULT | BLOCK_VERSION_RANDOMX;

    // Must match consensus.powLimit compact (main/test: >> 12; regtest: >> 1).
    arith_uint256 bnMain = ~arith_uint256(0) >> 12;
    arith_uint256 bnReg  = ~arith_uint256(0) >> 1;
    const uint32_t nBitsMain = bnMain.GetCompact();
    const uint32_t nBitsTest = nBitsMain;
    const uint32_t nBitsReg  = bnReg.GetCompact();

    printf("nBits main/test=0x%08x regtest=0x%08x\n", nBitsMain, nBitsReg);

    const char* ts_main =
        "EGA fair launch: equality of opportunity, not outcome — anyone may mine.";
    const char* ts_test =
        "EGA testnet: MultiShield-4 RandomX Verthash YespowerEGA Scrypt";
    const char* ts_reg =
        "EGA regtest MultiShield-4";

    // Fixed times (UTC) for reproducibility
    const uint32_t t_main = 1751846400; // 2025-07-07 00:00:00 UTC (near project start)
    const uint32_t t_test = 1751846401;
    const uint32_t t_reg  = 1751846402;

    std::string which = (argc > 1) ? argv[1] : "all";
    if (which == "main" || which == "all")
        Mine("main", ts_main, t_main, nBitsMain, nVersion);
    if (which == "test" || which == "all")
        Mine("test", ts_test, t_test, nBitsTest, nVersion);
    if (which == "regtest" || which == "all")
        Mine("regtest", ts_reg, t_reg, nBitsReg, nVersion);
    return 0;
}
