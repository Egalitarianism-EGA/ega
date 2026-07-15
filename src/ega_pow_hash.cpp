// EGA: CLI PoW hash for pool share verification (header + algo → hash).
// Usage: ega-pow-hash <algo> <header_hex>
//   algo: randomx | verthash | yespower-ega | scrypt | yespower
//   header_hex: 160 hex chars (80-byte Bitcoin-family header)
// Prints 64 hex chars (little-endian display order as uint256.GetHex()).

#include <crypto/ega_pow.h>
#include <primitives/block.h>
#include <uint256.h>
#include <utilstrencodings.h>

#include <cstdio>
#include <cstring>
#include <string>
#include <vector>

static void usage()
{
    std::fprintf(stderr, "usage: ega-pow-hash <algo> <header_hex_80_bytes>\n");
}

int main(int argc, char** argv)
{
    if (argc != 3) {
        usage();
        return 1;
    }
    std::string algo = argv[1];
    for (char& c : algo) {
        if (c >= 'A' && c <= 'Z')
            c = c - 'A' + 'a';
    }
    if (algo == "yespower")
        algo = "yespower-ega";

    std::vector<unsigned char> header = ParseHex(argv[2]);
    if (header.size() < 80) {
        std::fprintf(stderr, "header must be at least 80 bytes (got %zu)\n", header.size());
        return 1;
    }

    uint256 out;
    const unsigned char* p = header.data();
    // nTime is bytes 68..71 little-endian
    uint32_t nTime = (uint32_t)p[68] | ((uint32_t)p[69] << 8) | ((uint32_t)p[70] << 16) | ((uint32_t)p[71] << 24);

    if (algo == "randomx") {
        EgaRandomXHash(p, 80, nTime, out);
    } else if (algo == "verthash") {
        EgaVerthashHash(p, 80, out);
    } else if (algo == "yespower-ega") {
        EgaYespowerHash(p, 80, out);
    } else if (algo == "scrypt") {
        EgaScryptHash(p, 80, out);
    } else {
        std::fprintf(stderr, "unknown algo: %s\n", algo.c_str());
        return 1;
    }

    std::printf("%s\n", out.GetHex().c_str());
    return 0;
}
