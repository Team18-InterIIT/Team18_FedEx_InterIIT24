import unittest
from rectpack import newPacker
import matplotlib.pyplot as plt
import matplotlib.patches as patches


class TestRectPack(unittest.TestCase):
    def test_packing(self):
        # Create the packer
        packer = newPacker()

        # Add rectangles to pack
        packer.add_rect(50, 40)
        packer.add_rect(10, 20)
        packer.add_rect(80, 20)
        packer.add_rect(50, 20)
        packer.add_rect(30,40)

        # Add bins where the rectangles will be placed
        packer.add_bin(300, 300)

        # Start packing
        packer.pack()

        # Retrieve the list of packed rectangles
        packed_rects = packer.rect_list()

        # Plot the packed rectangles


        def plot_packed_rectangles(self, packed_rects, bin_width, bin_height):
            fig, ax = plt.subplots(1)
            ax.set_xlim(0, bin_width)
            ax.set_ylim(0, bin_height)
    
            for rect in packed_rects:
                print(rect)
                _, x, y, w, h , rid = rect
                ax.add_patch(patches.Rectangle((x, y), w, h, edgecolor='r', facecolor='none'))
    
            plt.gca().invert_yaxis()
            plt.savefig("output"+str(bin_width)+"+"+str(bin_height)+".png")
        plot_packed_rectangles(self, packed_rects, 300, 300)
if __name__ == '__main__':
    unittest.main()