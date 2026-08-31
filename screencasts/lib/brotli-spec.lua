-- @envy schema "1"
IDENTITY = "local.brotli@r0"
EXPORTABLE = true

OPTIONS = { version = { required = true } }

local hashes = {
  ["1.1.0"] = "e720a6ca29428b803f4ad165371771f5398faba397edf6778837a18599ea13ff",
}

FETCH = function(tmp_dir, opts)
  return {
    source = "https://github.com/google/brotli/archive/refs/tags/v" ..
        opts.version .. ".tar.gz",
    sha256 = hashes[opts.version],
  }
end

STAGE = { strip = 1 }

-- Google publishes no brotli binaries, so this builds one. Naming cmake and
-- ninja as products is what installs them ahead of BUILD and what makes
-- envy.product legal inside it. CMAKE_MAKE_PROGRAM is passed explicitly for
-- the same reason every path here is: nothing may come from PATH.
DEPENDENCIES = { { product = "cmake" }, { product = "ninja" } }

BUILD = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template([[
{{cmake}} -G Ninja -S . -B out -DCMAKE_BUILD_TYPE=Release -DCMAKE_MAKE_PROGRAM={{ninja}} -DCMAKE_INSTALL_PREFIX={{prefix}}
{{ninja}} -C out
]], {
    cmake = envy.product("cmake"),
    ninja = envy.product("ninja"),
    prefix = install_dir,
  })
end

INSTALL = function(install_dir, stage_dir, fetch_dir, tmp_dir, opts)
  return envy.template("{{ninja}} -C out install", { ninja = envy.product("ninja") })
end

PRODUCTS = { brotli = "bin/brotli" .. envy.EXE_EXT }
