const expect = require('chai').expect
const { stringToMask, maskToString, orMasks, composeMasks, addSelectedRows } = require('../support')

function MASK(...args) {
  return new Uint8Array(args)
}

describe('support', function () {
  describe('stringToMask', function () {
    it('should handle single numbers', function () {
      expect(stringToMask('1, 3, 4'))
        .to.deep.equal(MASK(1, 0, 1, 1))
    })

    it('should handle empty', function () {
      expect(stringToMask(''))
        .to.deep.equal(MASK())
    })

    it('should handle ranges', function () {
      expect(stringToMask('1-2, 4-5'))
        .to.deep.equal(MASK(1, 1, 0, 1, 1))
    })

    it('should handle length-1 ranges', function () {
      expect(stringToMask('1-1, 3-3'))
        .to.deep.equal(MASK(1, 0, 1))
    })

    it('should do nothing for zero- or negative-length ranges', function () {
      expect(stringToMask('2-1, 5-3'))
        .to.deep.equal(MASK())
    })

    it('should allow overlapping ranges', function () {
      expect(stringToMask('1-4, 2-5'))
        .to.deep.equal(MASK(1, 1, 1, 1, 1))
    })

    it('should ignore single-value zero', function () {
      expect(stringToMask('0'))
        .to.deep.equal(MASK())
    })

    it('should ignore zero in a range', function () {
      expect(stringToMask('0-2'))
        .to.deep.equal(MASK(1, 1))
    })

    it('should ignore too-many-values range', function () {
      expect(stringToMask('1-3-4'))
        .to.deep.equal(MASK())
    })

    it('should round down when given fractions', function () {
      expect(stringToMask('1.2, 3.1-4.8'))
        .to.deep.equal(MASK(1, 0, 1, 1))
    })

    it('should ignore non-numbers', function () {
      // Changing the retval here wouldn't be evil -- it's basically undefined
      // behavior. Mainly, we're testing that the output is reasonable and the
      // function doesn't crash.
      expect(stringToMask('1, foo-2, 3ef'))
        .to.deep.equal(MASK(1, 0, 1))
    })

    it('should limit range to a maximum', function () {
      expect(stringToMask('2-99', { maxMaskLength: 5 }))
        .to.deep.equal(MASK(0, 1, 1, 1, 1))
    })

    it('should limit single number to a maximum', function () {
      expect(stringToMask('2, 99', { maxMaskLength: 5 }))
        .to.deep.equal(MASK(0, 1))
    })

    it('should be speedy with big numbers', function () {
      expect(stringToMask('1-999999999999')).to.have.length(2000000)
    })
  })

  describe('maskToString', function () {
    it('should output single values', function () {
      expect(maskToString(MASK(1, 0, 1))).to.equal('1, 3')
    })

    it('should output ranges', function () {
      expect(maskToString(MASK(0, 1, 1, 0, 1, 1))).to.equal('2-3, 5-6')
    })
  })

  describe('orMasks', function () {
    it('should OR two masks', function () {
      expect(orMasks(MASK(1, 0, 0, 1), MASK(1, 1, 0, 0)))
        .to.deep.equal(MASK(1, 1, 0, 1))
    })

    it('should OR two masks when mask1 is longer', function () {
      expect(orMasks(MASK(1, 0, 0, 1), MASK(1, 1)))
        .to.deep.equal(MASK(1, 1, 0, 1))
    })

    it('should OR two masks when mask2 is longer', function () {
      expect(orMasks(MASK(0, 1), MASK(1, 0, 0, 1)))
        .to.deep.equal(MASK(1, 1, 0, 1))
    })
  })

  describe('composeMasks', function () {
    it('should compose masks', function () {
      // 1. Delete rows 1 and 4. Remaining rows: 2, 3, 5, 6, 7, ...
      // 2. Delete rows 2 and 3. Remaining rows: 2, 6, 7, ... (1, 3-5 deleted)
      expect(composeMasks(MASK(1, 0, 0, 1), MASK(0, 1, 1)))
        .to.deep.equal(MASK(1, 0, 1, 1, 1))
    })

    it('should add second-mask deletes after first mask ends', function () {
      // 1. Delete row 1. Remaining rows: 2, 3, 4, 5, ...
      // 2. Delete row 2. Remaining rows: 2, 4, 5, ... (1, 3 deleted)
      expect(composeMasks(MASK(1), MASK(0, 1)))
        .to.deep.equal(MASK(1, 0, 1))
    })

    it('should add first-mask deletes after second mask ends', function () {
      // 1. Delete row 3. Remaining rows: 1, 2, 4, 5, ...
      // 2. Delete row 1. Remaining rows: 2, 4, 5, ... (1, 3 deleted)
      expect(composeMasks(MASK(0, 0, 1), MASK(1)))
        .to.deep.equal(MASK(1, 0, 1))
    })

    it('should work when mask1[0] and mask[2] are false', function () {
      // 1. Delete rows 2, 4. Remaining rows: 1, 3, 5, 6, 7, 8, 9, ...
      // 2. Delete rows 2, 4. Remaining rows: 1, 5, 7, 8, 9, ... (2-4, 6 deleted)
      expect(composeMasks(MASK(0, 1, 0, 1), MASK(0, 1, 0, 1)))
        .to.deep.equal(MASK(0, 1, 1, 1, 0, 1))
    })

    it('should work when mask1 is all at beginning', function () {
      // 1. Delete rows 1-3. Remaining rows: 4, 5, 6, 7, 8, 9, ...
      // 2. Delete rows 2-3. Remaining rows: 4, 7, 8, 9, ... (1-3, 5-6 deleted)
      expect(composeMasks(MASK(1, 1, 1), MASK(0, 1, 1)))
        .to.deep.equal(MASK(1, 1, 1, 0, 1, 1))
    })

    it('should work when mask2 is all at beginning', function () {
      // 1. Delete rows 2-3. Remaining rows: 1, 4, 5, 6, 7, 8, 9, ...
      // 2. Delete rows 1-3. Remaining rows: 6, 7, 8, 9, ... (1-5 deleted)
      expect(composeMasks(MASK(0, 1, 1), MASK(1, 1, 1)))
        .to.deep.equal(MASK(1, 1, 1, 1, 1))
    })

    it('should work when mask2 is all before mask1', function () {
      // 1. Delete rows 4-5. Remaining rows: 1, 2, 3, 6, 7, 8, ...
      // 2. Delete rows 1-2. Remaining rows: 3, 6, 7, 8, ... (1-2, 4-5 deleted)
      expect(composeMasks(MASK(0, 0, 0, 1, 1), MASK(1, 1)))
        .to.deep.equal(MASK(1, 1, 0, 1, 1))
    })
  })

  describe('addSelectedRows', function () {
    it('should OR when adding deletions to input', function () {
      expect(addSelectedRows({ rows: '8-9' }, '2-3', true))
        .to.deep.equal({ rows: '2-3, 8-9' })
    })

    it('should COMPOSE when adding deletions to output', function () {
      expect(addSelectedRows({ rows: '1-3' }, '2-3', false))
        .to.deep.equal({ rows: '1-3, 5-6' })
    })

    it('should convert from schema-v0 to schema-v1 before compose', function () {
      expect(addSelectedRows({ rows: '', first_row: 1, last_row: 3 }, '2-3', false))
        .to.deep.equal({ first_row: 0, last_row: 0, rows: '1-3, 5-6' })
    })

    it('should be speedy with big numbers', function () {
      expect(addSelectedRows({ rows: '999999' }, '234012', false))
        .to.deep.equal({ rows: '234012, 999999' })
    })

    it('should nix excessively-large numbers', function () {
      expect(addSelectedRows({ rows: '999999999' }, '234012', false))
        .to.deep.equal({ rows: '234012' })
    })
  })
})
