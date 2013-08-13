import baseclass
import unittest
import storage.devicelibs.swap as swap

class SwapTestCase(baseclass.DevicelibsTestCase):

    def testSwap(self):
        ##
        ## mkswap
        ##
        # pass
        self.assertEqual(swap.mkswap(self._LOOP_DEV0, "swap"), None)

        # fail
        self.assertRaises(swap.SwapError, swap.mkswap, "/not/existing/device")
        
        ##
        ## swapon
        ##
        # pass
        self.assertEqual(swap.swapon(self._LOOP_DEV0, 1), None)

        # fail
        self.assertRaises(swap.SwapError, swap.swapon, "/not/existing/device")
        # not a swap partition
        self.assertRaises(swap.SwapError, swap.swapon, self._LOOP_DEV1)
        
        # pass
        # make another swap
        self.assertEqual(swap.mkswap(self._LOOP_DEV1, "another-swap"), None)
        self.assertEqual(swap.swapon(self._LOOP_DEV1), None)

        ##
        ## swapstatus
        ##
        # pass
        self.assertEqual(swap.swapstatus(self._LOOP_DEV0), True)
        self.assertEqual(swap.swapstatus(self._LOOP_DEV1), True)
        
        # does not fail
        self.assertEqual(swap.swapstatus("/not/existing/device"), False)

        ##
        ## swapoff
        ##
        # pass
        self.assertEqual(swap.swapoff(self._LOOP_DEV1), None)

        # check status
        self.assertEqual(swap.swapstatus(self._LOOP_DEV0), True)
        self.assertEqual(swap.swapstatus(self._LOOP_DEV1), False)

        self.assertEqual(swap.swapoff(self._LOOP_DEV0), None)

        # fail
        self.assertRaises(swap.SwapError, swap.swapoff, "/not/existing/device")
        # already off
        self.assertRaises(swap.SwapError, swap.swapoff, self._LOOP_DEV0)


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(SwapTestCase)


if __name__ == "__main__":
    unittest.main()
