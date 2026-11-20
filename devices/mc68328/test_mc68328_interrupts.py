# license:BSD-3-Clause
"""Compile the production interrupt-update methods with a minimal CPU-line fixture.

Checks MC68EZ328 UM 6.6.3-6.6.5 / MC68328 UM 6.5.3, 6.5.5-6.5.6.
The fixture groups two sources at level 4 and one at level 5; it does not
replace or duplicate the methods under test.
"""
import pathlib
import os
import subprocess
import tempfile
import unittest


class InterruptTest(unittest.TestCase):
    def test_pending_mask_status_and_shared_level(self):
        root = pathlib.Path(os.environ['MAME_SOURCE_ROOT'])
        source = (root / 'src/devices/machine/mc68328.cpp').read_text()
        start = source.index('void mc68328_base_device::update_ipr_state(')
        end = source.index('void mc68328_base_device::set_interrupt_line(', start)
        fixture = r'''
#include <cstdint>
#include <cassert>
using u32 = uint32_t;
constexpr int ASSERT_LINE=1, CLEAR_LINE=0;
class mc68328_base_device {
public:
    u32 m_ipr=0, m_imr=~0U, m_gisr=0;
    bool lines[8]{};
    int get_irq_level_for_mask(u32 m) { return m&4 ? 5 : m&3 ? 4 : 0; }
    u32 get_irq_mask_for_level(int l) { return l==5 ? 4 : l==4 ? 3 : 0; }
    void set_input_line(int l, int s) { lines[l]=s; }
    void update_ipr_state(u32);
    void update_imr_state(u32);
    void request(u32 bit, bool active) {
        if(active) m_ipr|=bit; else m_ipr&=~bit;
        update_ipr_state(bit);
    }
    void mask(u32 m) {
        auto changed=m_imr^m; m_imr=m; update_imr_state(changed);
    }
};
'''
        checks = r'''
int main() {
    mc68328_base_device c;
    c.request(4, true); // masked request is visible only in IPR
    assert(c.m_ipr==4 && c.m_gisr==0 && !c.lines[5]);
    c.mask(~4U);
    assert(c.m_gisr==4 && c.lines[5]);
    c.mask(~0U);
    assert(c.m_ipr==4 && c.m_gisr==0 && !c.lines[5]);
    c.mask(~4U); // reassert after mask/unmask without a new peripheral edge
    assert(c.m_gisr==4 && c.lines[5]);
    c.request(4, false);
    assert(c.m_gisr==0 && !c.lines[5]);
    c.mask(~7U);
    c.request(1, true); c.request(2, true);
    assert(c.m_gisr==3 && c.lines[4]);
    c.mask(~6U); // source 2 must keep the shared level asserted
    assert(c.m_ipr==3 && c.m_gisr==2 && c.lines[4]);
    c.request(1, true); // a masked source cannot appear in ISR
    assert(c.m_gisr==2 && c.lines[4]);
    c.request(2, false);
    assert(c.m_ipr==1 && c.m_gisr==0 && !c.lines[4]);
    c.mask(~5U); // simultaneously change masks at two different levels
    c.request(4, true);
    assert(c.m_gisr==5 && c.lines[4] && c.lines[5]);
    c.mask(~0U);
    assert(c.m_ipr==5 && c.m_gisr==0 && !c.lines[4] && !c.lines[5]);
}
'''
        with tempfile.TemporaryDirectory(prefix='mc68328-irq-') as directory:
            cpp = pathlib.Path(directory) / 'test.cpp'
            exe = pathlib.Path(directory) / 'test'
            cpp.write_text(fixture + source[start:end] + checks)
            subprocess.run(['c++', '-std=c++17', '-Wall', '-Wextra', '-Werror', str(cpp), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)
