const DefaultOptions = {
  maxMaskLength: 2000000 // bound memory/CPU usage
}

// Internal logic is done using Uint8Array. It's almost as easy to use as an
// Array of booleans, and it's much faster/smaller. One can imagine smaller or
// faster data structures, but they'd be more complex.
//
// And yes, we need the space. With 1M entries, an Array of boolean costs
// 27MB more than a Uint8Array.
//
// $ node
// > a = []; for (let i = 0; i < 1000000; i++) { a[i] = (i % 2 === 1) }
// true
// > process.memoryUsage().
// { rss: 60563456,
//   heapTotal: 38899712,
//   heapUsed: 34884296,
//   external: 8613 }
// > process.exit()
// $ node
// > a = new Uint8Array(1000000); for (let i = 0; i < 1000000; i++) { a[i] = (i % 2 === 1) }
// true
// > process.memoryUsage()
// { rss: 31313920,
//   heapTotal: 7684096,
//   heapUsed: 5291464,
//   external: 1008688 }

function stringToMask (str, options) {
  if (!options) options = {}
  options = { ...DefaultOptions, ...options }
  const { maxMaskLength } = options

  const spans = str.split(/,/g) // split by comma

    // Parse "A-B" into [A, B] numeric ranges, zero-indexed.
    .map(s => s.split('-')
      .map(s2 => parseInt(s2.trim(), 10) - 1)
    )
    .filter(s => s.length === 1 || s.length === 2) // ignore wrong-length spans
    .map(s => s.length === 1 ? [ s, s ] : s)       // turn `A` into `[A, A]`
    .filter(([a, b]) => !isNaN(a) && !isNaN(b))    // nix parse errors
    .map(([a, b]) => [ Math.max(0, a), Math.min(maxMaskLength - 1, b) ]) // bound
    .filter(([a, b]) => a <= b)                    // nix 0- or negative-length spans

  // Output length is whatever the maximum number in the values/ranges.
  const len = spans.reduce((agg, s) => Math.max(agg, s[1] + 1), 0)

  const mask = new Uint8Array(len)

  for (const [ begin, end ] of spans) {
    for (let i = begin; i <= end; i++) {
      mask[i] = 1
    }
  }

  return mask
}

/**
 * OR two masks of booleans.
 *
 * Why: if we already deleted for 2 and we're asked to delete row 2 again, then
 * OR is the operation we need: its output will be, 'Delete row 2'.
 *
 * @param mask1 One mask
 * @param mask2 Another mask
 */
function orMasks (mask1, mask2) {
  const shortMask = mask1.length < mask2.length ? mask1 : mask2
  const longMask = shortMask === mask1 ? mask2 : mask1
  const shortLen = shortMask.length

  const mask = new Uint8Array(longMask)
  for (let i = 0; i < shortLen; i++) {
    mask[i] = mask[i] || shortMask[i]
  }

  return mask
}

/**
 * Apply mask2 on top of the output of mask1.
 *
 * Why: if we deleted row 2 and are asked to delete rows 1-3 of the output of
 * that first delete operation, then COMPOSE is the operation we need: its
 * output will be, 'Delete rows 1-4'.
 *
 * Order of arguments matters:
 *
 *     compose(2, 1-3) => 1-4
 *     compose(1-3, 2) => 1-3, 5
 *
 * @param mask1 The original mask
 * @param mask2 A mask to apply to the output from applying mask1
 */
function composeMasks (mask1, mask2) {
  const len1 = mask1.length
  const len2 = mask2.length

  // Output length is hard to guess. Let's just double the RAM and truncate.
  const mask = new Uint8Array(len1 + len2)
  // Walk through the elements of `mask` (with pointer j). Delete according to
  // mask1 and mask2, which we iterate over using i1 and i2.
  let j = 0
  for (let i1 = 0, i2 = 0; i1 < mask1.length || i2 < mask2.length; j++) {
    if (i1 < len1 && mask1[i1]) {
      // Element is deleted, according to mask1. Mark it as such before even
      // checking against mask1.
      mask[j] = true
      i1++
    } else {
      // Apply mask2 and move forward
      mask[j] = i2 < len2 && mask2[i2]
      i2++
      i1++
    }
  }

  // Truncate so the last value is `true`
  return new Uint8Array(mask.slice(0, j))
}

function maskToString (mask) {
  const len = mask.length
  const spans = []

  let spanStart = null
  for (let i = 0; i < len; i++) {
    const bit = mask[i]
    if (bit && spanStart === null) {
      spanStart = i
    } else if (!bit && spanStart !== null) {
      spans.push([ spanStart, i - 1 ])
      spanStart = null
    }
  }
  if (spanStart !== null) {
    spans.push([ spanStart, len - 1 ])
  }

  return spans
    .map(span => span[0] === span[1] ? String(span[0] + 1) : `${span[0] + 1}-${span[1] + 1}`)
    .join(', ')
}

/**
 * Build changed params to incorporate the new selectedRows.
 *
 * @param oldParams Old Object params.
 * @param addRows String of new row numbers, e.g. '1-5, 8'
 * @param fromInput Boolean: true means the user selected addRows on the input
 *                  table; true means the user selected addRows on the output
 *                  table.
 */
function addSelectedRows (oldParams, addRows, fromInput) {
  const ret = {}
  let oldRows

  if (oldParams.first_row && oldParams.last_row && !oldParams.rows) {
    ret.first_row = 0
    ret.last_row = 0
    oldRows = [ oldParams.first_row, oldParams.last_row ].join('-')
  } else {
    oldRows = oldParams.rows || ''
  }

  const oldMask = stringToMask(oldRows)
  const addMask = stringToMask(addRows)
  let newMask
  if (fromInput) {
    newMask = orMasks(oldMask, addMask)
  } else {
    newMask = composeMasks(oldMask, addMask)
  }

  ret.rows = maskToString(newMask)

  return ret
}

module.exports = {
  stringToMask,
  orMasks,
  composeMasks,
  maskToString,
  addSelectedRows
}
