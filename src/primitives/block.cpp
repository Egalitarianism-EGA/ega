// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2019 The Bitcoin Core developers
// Copyright (c) 2014-2019 The DigiByte Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <primitives/block.h>
#include <crypto/ega_pow.h>
#include <hash.h>
#include <tinyformat.h>
#include <utilstrencodings.h>
#include <crypto/common.h>
#include <arith_uint256.h>
#include <consensus/params.h>
#include <consensus/consensus.h>
#include <algorithm>

uint256 CBlockHeader::GetHash() const
{
    return SerializeHash(*this);
}

int CBlockHeader::GetAlgo() const
{
    switch (nVersion & BLOCK_VERSION_ALGO)
    {
        case BLOCK_VERSION_RANDOMX:
            return ALGO_RANDOMX;
        case BLOCK_VERSION_SCRYPT:
            return ALGO_SCRYPT;
        case BLOCK_VERSION_VERTHASH:
            return ALGO_VERTHASH;
        case BLOCK_VERSION_YESPOWER_EGA:
            return ALGO_YESPOWER_EGA;
        default:
            return ALGO_UNKNOWN;
    }
}

uint32_t OdoKey(const Consensus::Params& params, uint32_t nTime)
{
    uint32_t nShapechangeInterval = params.nOdoShapechangeInterval;
    return nTime - nTime % nShapechangeInterval;
}

uint256 CBlockHeader::GetPoWAlgoHash(const Consensus::Params& params) const
{
    return EgaGetPoWHash(*this, params);
}

std::string CBlock::ToString(const Consensus::Params& params) const
{
    std::stringstream s;
    s << strprintf("CBlock(hash=%s, ver=0x%08x, pow_algo=%d, pow_hash=%s, hashPrevBlock=%s, hashMerkleRoot=%s, nTime=%u, nBits=%08x, nNonce=%u, vtx=%u)\n",
        GetHash().ToString(),
        nVersion,
        GetAlgo(),
        GetPoWAlgoHash(params).ToString(),
        hashPrevBlock.ToString(),
        hashMerkleRoot.ToString(),
        nTime, nBits, nNonce,
        vtx.size());
    for (const auto& tx : vtx) {
        s << "  " << tx->ToString() << "\n";
    }
    return s.str();
}

std::string GetAlgoName(int Algo)
{
    switch (Algo)
    {
        case ALGO_RANDOMX:
            return std::string("randomx");
        case ALGO_VERTHASH:
            return std::string("verthash");
        case ALGO_YESPOWER_EGA:
            return std::string("yespower-ega");
        case ALGO_SCRYPT:
            return std::string("scrypt");
        default:
            return std::string("unknown");
    }
}

int GetAlgoByName(std::string strAlgo, int fallback)
{
    transform(strAlgo.begin(),strAlgo.end(),strAlgo.begin(),::tolower);
    if (strAlgo == "randomx" || strAlgo == "rx")
        return ALGO_RANDOMX;
    else if (strAlgo == "verthash" || strAlgo == "vtc" || strAlgo == "vert")
        return ALGO_VERTHASH;
    else if (strAlgo == "yespower-ega" || strAlgo == "yespower" || strAlgo == "yp" || strAlgo == "yespowerega")
        return ALGO_YESPOWER_EGA;
    else if (strAlgo == "scrypt")
        return ALGO_SCRYPT;
    else
        return fallback;
}

int64_t GetBlockWeight(const CBlock& block)
{
    return ::GetSerializeSize(block, SER_NETWORK, PROTOCOL_VERSION | SERIALIZE_TRANSACTION_NO_WITNESS) * (WITNESS_SCALE_FACTOR - 1) + ::GetSerializeSize(block, SER_NETWORK, PROTOCOL_VERSION);
}
