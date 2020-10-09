import unittest
from router import simplerouter, distancerouter


knownpeers = {
    "p01": ("h1", "p1"),
    "p02": ("h2", "p2"),
    "p03": ("h3", "p3"),
    "p04": ("h4", "p4")
}

maxpeers = 1024

class TestRoutingMethods(unittest.TestCase):


    def __assertresponse(self, targetpeer, nextpeer, host, port):
        self.assertEqual(nextpeer, targetpeer)
        self.assertEqual(host, knownpeers[targetpeer][0])
        self.assertEqual(port, knownpeers[targetpeer][1])


    def __assertnone(self, nextpeer, host, port):
        self.assertEqual(nextpeer, None)
        self.assertEqual(host, None)
        self.assertEqual(port, None)


    def test_local_peer(self):
        for r in [simplerouter, distancerouter]:
            with self.subTest(r=r):
                targetpeer = "p01"
                nextpeer, host, port = r(targetpeer, knownpeers, maxpeers, set())
                self.__assertresponse(targetpeer, nextpeer, host, port)


    def test_all_discarded(self):
        for r in [simplerouter, distancerouter]:
            with self.subTest(r=r):
                targetpeer = "p99"
                nextpeer, host, port = r(targetpeer, knownpeers, maxpeers, set(knownpeers.keys()))
                self.__assertnone(nextpeer, host, port)


    def test_simple_unknown_peer(self):
        targetpeer = "p99"
        nextpeer, host, port = simplerouter(targetpeer, knownpeers, maxpeers, set())
        self.__assertresponse("p01", nextpeer, host, port)


    def test_distance_unknown_peer(self):
        targetpeer = "p99"
        nextpeer, host, port = distancerouter(targetpeer, knownpeers, maxpeers, set())
        self.__assertresponse("p04", nextpeer, host, port)


    def test_distance_some_discarded(self):
        targetpeer = "p99"
        nextpeer, host, port = distancerouter(targetpeer, knownpeers, maxpeers, set({"p04"}))
        self.__assertresponse("p03", nextpeer, host, port)


    def test_distance_no_peers(self):
        targetpeer = "p99"
        with self.assertRaises(AssertionError):
            distancerouter(targetpeer, knownpeers, 1, set())


if __name__ == '__main__':
    unittest.main()