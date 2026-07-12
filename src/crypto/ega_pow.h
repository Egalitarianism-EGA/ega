// Copyright (c) 2026 The EGA Core developers
// Distributed under the MIT software license.

#ifndef EGA_POW_H
#define EGA_POW_H

#include <uint256.h>
#include <primitives/block.h>

class CBlockHeader;

namespace Consensus { struct Params; }

/** Compute PoW hash for the given block header (algo selected from version bits). */
uint256 EgaGetPoWHash(const CBlockHeader& header, const Consensus::Params& params);

/** YespowerEGA parameters (frozen). N=2048, r=32 ≈ 256 KiB; personalization "YespowerEGA". */
void EgaYespowerHash(const unsigned char* input, size_t input_len, uint256& output);

/** RandomX (light VM) with epoch seed derived from header time. */
void EgaRandomXHash(const unsigned char* input, size_t input_len, uint32_t nTime, uint256& output);

/** Verthash with EGA-personalized in-memory dataset (see docs/ega/params.md). */
void EgaVerthashHash(const unsigned char* input, size_t input_len, uint256& output);

#endif // EGA_POW_H
