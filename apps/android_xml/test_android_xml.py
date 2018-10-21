import tempfile
from io import BytesIO
from django.test import TestCase
import xml.etree.ElementTree as ET

from ..hero_advantages.factories import HeroFactory
from ..hero_abilities.factories import AbilityFactory

from . import AndroidXml


class TestAndroidXml(TestCase):
    def setUp(self):
        earthshaker = HeroFactory(name='Earthshaker')
        HeroFactory(name='Disruptor')
        AbilityFactory(
            hero=earthshaker,
            name='Fissure',
            cooldown='18/17/16/15',
        )
        AbilityFactory(
            hero=earthshaker,
            name='Rock spell',
        )

    def test_xml_fundamentals(self):
        # There must be an easier way to do this!
        with tempfile.NamedTemporaryFile() as f:
            f.write(AndroidXml.generate(update_first=False))
            f.seek(0)
            tree = ET.parse(f.name)
        assert tree.getroot().tag == 'listOfHeroInfo'
        assert len(tree.getroot()) == 2
        assert tree.getroot()[0].tag == 'heroInfo'

        earthshaker = next(h for h in tree.getroot() if h.find('name').text == 'Earthshaker')
        abilities = earthshaker.findall('abilities')
        assert len(abilities) == 2
        fissure = next(a for a in abilities if a.find('name').text == 'Fissure')
        assert fissure.find('cooldown').text == '18/17/16/15'

    def test_wip_real_xml(self):
        tree = ET.parse('/home/paul/code/true-sight-backend/hero_info_from_web.xml')
        assert tree.getroot().tag == 'listOfHeroInfo'
        assert tree.getroot()[0].tag == 'heroInfo'

        earthshaker = next(h for h in tree.getroot() if h.find('name').text == 'Earthshaker')
        abilities = earthshaker.findall('abilities')
        assert len(abilities) == 4
        fissure = next(a for a in abilities if a.find('name').text == 'Fissure')
        assert fissure.find('cooldown').text == '18/17/16/15'
