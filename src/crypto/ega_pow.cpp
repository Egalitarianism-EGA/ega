// Copyright (c) 2026 The EGA Core developers
// Distributed under the MIT software license.
//
// EGA triple PoW: RandomX + Verthash + YespowerEGA

#include <crypto/ega_pow.h>

#include <crypto/sha256.h>
#include <hash.h>
#include <primitives/block.h>
#include <serialize.h>
#include <streams.h>
#include <version.h>
#include <uint256.h>
#include <arith_uint256.h>
#include <consensus/params.h>

#include <mutex>
#include <vector>
#include <cstring>
#include <cstdlib>
#include <algorithm>

extern "C" {
#include <crypto/yespower/yespower.h>
#include <crypto/verthash/verthash.h>
#include <randomx.h>
}

// ---- YespowerEGA ----
// N=2048, r=32 → 256 KiB working memory (old phones / Pi friendly).
// Personalization binds work to EGA only (no merge-mine with other yespower coins).
static const yespower_params_t YESPOWER_EGA_PARAMS = {
    YESPOWER_1_0,
    2048,
    32,
    (const uint8_t*)"YespowerEGA",
    11
};

void EgaYespowerHash(const unsigned char* input, size_t input_len, uint256& output)
{
    yespower_binary_t dst;
    if (yespower_tls(input, input_len, &YESPOWER_EGA_PARAMS, &dst) != 0) {
        // On failure, force invalid work (max hash)
        output = ArithToUint256(~arith_uint256(0));
        return;
    }
    static_assert(sizeof(dst.uc) == 32, "yespower hash size");
    memcpy(output.begin(), dst.uc, 32);
}

// ---- RandomX (light mode) ----
// Seed epoch: nTime / (2048 * 60) so cache rebuilds ~every 2048 minutes (~1.4 days),
// without needing block height in the header hash API.
static std::mutex g_rx_mutex;
static randomx_cache* g_rx_cache = nullptr;
static randomx_vm* g_rx_vm = nullptr;
static uint32_t g_rx_epoch = UINT32_MAX;

static void EgaRandomXEnsure(uint32_t nTime)
{
    const uint32_t epoch = nTime / (2048u * 60u);
    if (g_rx_vm && epoch == g_rx_epoch)
        return;

    if (g_rx_vm) {
        randomx_destroy_vm(g_rx_vm);
        g_rx_vm = nullptr;
    }
    if (g_rx_cache) {
        randomx_release_cache(g_rx_cache);
        g_rx_cache = nullptr;
    }

    randomx_flags flags = randomx_get_flags();
    // Light mode: no FULL_MEM dataset (works on low RAM; miners may upgrade later).
    g_rx_cache = randomx_alloc_cache(flags);
    if (!g_rx_cache) {
        return;
    }

    // Seed = SHA256("EGA-RandomX" || le32(epoch))
    CSHA256 hasher;
    const char tag[] = "EGA-RandomX";
    hasher.Write((const unsigned char*)tag, sizeof(tag) - 1);
    unsigned char le[4] = {
        (unsigned char)(epoch),
        (unsigned char)(epoch >> 8),
        (unsigned char)(epoch >> 16),
        (unsigned char)(epoch >> 24)
    };
    hasher.Write(le, 4);
    unsigned char seed[32];
    hasher.Finalize(seed);

    randomx_init_cache(g_rx_cache, seed, sizeof(seed));
    g_rx_vm = randomx_create_vm(flags, g_rx_cache, nullptr);
    g_rx_epoch = epoch;
}

void EgaRandomXHash(const unsigned char* input, size_t input_len, uint32_t nTime, uint256& output)
{
    std::lock_guard<std::mutex> lock(g_rx_mutex);
    EgaRandomXEnsure(nTime);
    if (!g_rx_vm) {
        output = ArithToUint256(~arith_uint256(0));
        return;
    }
    char hash[RANDOMX_HASH_SIZE];
    randomx_calculate_hash(g_rx_vm, input, input_len, hash);
    memcpy(output.begin(), hash, 32);
}

// ---- Verthash (EGA dataset) ----
// Same seeking algorithm as Vertcoin Verthash; dataset is EGA-personalized and
// sized for practical node bootstrap (256 MiB). Documented in docs/ega/params.md.
static const size_t EGA_VERTHASH_DATASET_SIZE = 256ull * 1024ull * 1024ull;
static std::mutex g_vh_mutex;
static std::vector<unsigned char> g_vh_dataset;
static bool g_vh_ready = false;

static void EgaVerthashEnsureDataset()
{
    if (g_vh_ready)
        return;

    g_vh_dataset.resize(EGA_VERTHASH_DATASET_SIZE);
    // Expand deterministic blob: repeated SHA256("EGA-Verthash-v1" || index)
    const char tag[] = "EGA-Verthash-v1";
    size_t offset = 0;
    uint64_t index = 0;
    while (offset < EGA_VERTHASH_DATASET_SIZE) {
        CSHA256 hasher;
        hasher.Write((const unsigned char*)tag, sizeof(tag) - 1);
        unsigned char idx[8];
        for (int i = 0; i < 8; i++)
            idx[i] = (unsigned char)((index >> (8 * i)) & 0xff);
        hasher.Write(idx, 8);
        unsigned char block[32];
        hasher.Finalize(block);
        size_t n = std::min(sizeof(block), EGA_VERTHASH_DATASET_SIZE - offset);
        memcpy(g_vh_dataset.data() + offset, block, n);
        offset += n;
        index++;
    }
    g_vh_ready = true;
}

void EgaVerthashHash(const unsigned char* input, size_t input_len, uint256& output)
{
    std::lock_guard<std::mutex> lock(g_vh_mutex);
    EgaVerthashEnsureDataset();
    unsigned char out[32];
    verthash_hash(g_vh_dataset.data(), g_vh_dataset.size(), input, input_len, out);
    memcpy(output.begin(), out, 32);
}

// ---- Dispatch ----
static void SerializeHeader(const CBlockHeader& header, std::vector<unsigned char>& out)
{
    CDataStream ss(SER_NETWORK, PROTOCOL_VERSION);
    ss << header;
    out.assign(ss.begin(), ss.end());
}

uint256 EgaGetPoWHash(const CBlockHeader& header, const Consensus::Params& params)
{
    (void)params;
    std::vector<unsigned char> data;
    SerializeHeader(header, data);

    uint256 result;
    switch (header.GetAlgo()) {
    case ALGO_RANDOMX:
        EgaRandomXHash(data.data(), data.size(), header.nTime, result);
        return result;
    case ALGO_VERTHASH:
        EgaVerthashHash(data.data(), data.size(), result);
        return result;
    case ALGO_YESPOWER_EGA:
        EgaYespowerHash(data.data(), data.size(), result);
        return result;
    default:
        return ArithToUint256(~arith_uint256(0));
    }
}
