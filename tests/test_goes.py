from __future__ import absolute_import

import copy
import datetime
import pytest

import numpy as np
from astropy.units.quantity import Quantity

from sunpy.time import TimeRange
from sunpy.instr import goes
import sunpy.lightcurve as lc
from pandas.util.testing import assert_frame_equal

@pytest.mark.online
def test_goes_event_list():
    # Set a time range to search
    trange = TimeRange('2011-06-07 00:00', '2011-06-08 00:00')
    # Test case where GOES class filter is applied
    result = goes.get_goes_event_list(trange, goes_class_filter='M1')
    assert type(result) == list
    assert type(result[0]) == dict
    assert type(result[0]['event_date'] == str)
    assert type(result[0]['goes_location'] == tuple)
    assert type(result[0]['peak_time'] == datetime)
    assert type(result[0]['start_time'] == datetime)
    assert type(result[0]['end_time'] == datetime)
    assert type(result[0]['goes_class'] == str)
    assert type(result[0]['noaa_active_region'] == int)
    assert result[0]['event_date'] == '2011-06-07'
    assert result[0]['goes_location'] == (54, -21)
    assert result[0]['start_time'] == datetime.datetime(2011, 6, 7, 6, 16)
    assert result[0]['peak_time'] == datetime.datetime(2011, 6, 7, 6, 41)
    assert result[0]['end_time'] == datetime.datetime(2011, 6, 7, 6, 59)
    assert result[0]['goes_class'] == 'M2.5'
    assert result[0]['noaa_active_region'] == 11226
    # Test case where GOES class filter not applied
    result = goes.get_goes_event_list(trange)
    assert type(result) == list
    assert type(result[0]) == dict
    assert type(result[0]['event_date'] == str)
    assert type(result[0]['goes_location'] == tuple)
    assert type(result[0]['peak_time'] == datetime)
    assert type(result[0]['start_time'] == datetime)
    assert type(result[0]['end_time'] == datetime)
    assert type(result[0]['goes_class'] == str)
    assert type(result[0]['noaa_active_region'] == int)
    assert result[0]['event_date'] == '2011-06-07'
    assert result[0]['goes_location'] == (54, -21)
    assert result[0]['start_time'] == datetime.datetime(2011, 6, 7, 6, 16)
    assert result[0]['peak_time'] == datetime.datetime(2011, 6, 7, 6, 41)
    assert result[0]['end_time'] == datetime.datetime(2011, 6, 7, 6, 59)
    assert result[0]['goes_class'] == 'M2.5'
    assert result[0]['noaa_active_region'] == 11226


@pytest.mark.online
def test_temp_em():
    # Create GOESLightcurve object, then create new one with
    # temperature & EM using with temp_em().
    goeslc = lc.GOESLightCurve.create("2014-01-01 00:00", "2014-01-01 01:00")
    goeslc_new = goes.temp_em(goeslc)
    # Test correct exception is raised if a GOESLightCurve object is
    # not inputted.
    with pytest.raises(TypeError):
        goes.temp_em([])
    # Find temperature and EM manually with goes_chianti_tem()
    temp, em = goes.goes_chianti_tem(
        Quantity(goeslc.data.xrsb, unit='W/m**2'),
        Quantity(goeslc.data.xrsa, unit='W/m**2'),
        satellite=int(goeslc.meta["TELESCOP"].split()[1]), date="2014-01-01")
    # Check that temperature and EM arrays from goes_chianti_tem()
    # are same as those in new GOESLightcurve object.
    assert goeslc_new.data.temperature.all() == temp.value.all()
    assert goeslc_new.data.em.all() == em.value.all()
    # Check rest of data frame of new GOESLightCurve object is same
    # as that in original object.
    goeslc_revert = copy.deepcopy(goeslc_new)
    del goeslc_revert.data["temperature"]
    del goeslc_revert.data["em"]
    assert_frame_equal(goeslc_revert.data, goeslc.data)

@pytest.mark.online
def test_goes_chianti_tem():
    longflux = Quantity([7e-6], unit="W/m**2")
    shortflux = Quantity([7e-7], unit="W/m**2")
    ratio = shortflux/longflux
    shortflux_toomany = Quantity(
        np.append(shortflux.value, shortflux.value[0]), unit="W/m**2")
    shortflux_toosmall = copy.deepcopy(shortflux)
    shortflux_toosmall.value[0] = -1
    shortflux_toobig = copy.deepcopy(shortflux)
    shortflux_toobig.value[0] = 1
    temp_test = Quantity(np.zeros(len(longflux))+10, unit="MK")
    temp_test_toomany = Quantity(np.append(temp_test, 0), unit="MK")
    temp_test_toosmall = copy.deepcopy(temp_test)
    temp_test_toosmall.value[0] = -1
    temp_test_toobig = copy.deepcopy(temp_test)
    temp_test_toobig.value[0] = 101
    date = "2014-04-16"
    # First test correct exceptions are raised if incorrect inputs are
    # entered.
    with pytest.raises(ValueError):
        temp, em = goes.goes_chianti_tem(longflux, shortflux, satellite=-1)
    with pytest.raises(ValueError):
        temp, em = goes.goes_chianti_tem(longflux, shortflux_toomany)
    with pytest.raises(ValueError):
        temp = goes._goes_get_chianti_temp(ratio, satellite=-1)
    with pytest.raises(ValueError):
        temp, em = goes.goes_chianti_tem(longflux, shortflux,
                                         abundances="Neither")
    with pytest.raises(ValueError):
        temp = goes._goes_get_chianti_temp(ratio, abundances="Neither")
    with pytest.raises(ValueError):
        temp, em = goes.goes_chianti_tem(longflux, shortflux_toobig)
    with pytest.raises(ValueError):
        em = goes._goes_get_chianti_em(longflux, temp_test, satellite=-1)
    with pytest.raises(ValueError):
        em = goes._goes_get_chianti_em(longflux, temp_test,
                                       abundances="Neither")
    with pytest.raises(ValueError):
        em = goes._goes_get_chianti_em(longflux, temp_test,
                                       abundances="Neither")
    with pytest.raises(ValueError):
        em = goes._goes_get_chianti_em(longflux, temp_test_toosmall)
    with pytest.raises(ValueError):
        em = goes._goes_get_chianti_em(longflux, temp_test_toobig)

    # test case 1: satellite > 7, abundances = coronal
    temp1, em1 = goes.goes_chianti_tem(longflux, shortflux, satellite=15,
                                       date=date)
    np.testing.assert_allclose(temp1, Quantity([11.28], unit="MK"), rtol=0.01)
    assert all(em1 < Quantity([4.79e+48], unit="1/cm**3")) and \
      em1 > Quantity([4.78e+48], unit="1/cm**3")

    # test case 2: satellite > 7, abundances = photospheric
    temp2, em2 = goes.goes_chianti_tem(longflux, shortflux, satellite=15,
                                       date=date, abundances="photospheric")
    assert all(temp2 < Quantity([10.25], unit="MK")) and \
      all(temp2 > Quantity([10.24], unit="MK"))
    assert all(em2 < Quantity([1.12e+49], unit="1/cm**3")) and \
      all(em2 > Quantity([1.11e+49], unit="1/cm**3"))

    # test case 3: satellite < 8 and != 6, abundances = coronal
    temp3, em3 = goes.goes_chianti_tem(longflux, shortflux, satellite=5,
                                       date=date,
                                       abundances="coronal")
    assert all(temp3 < Quantity([11.43], unit="MK")) and \
      all(temp3 > Quantity([11.42], unit="MK"))
    assert all(em3 < Quantity([3.85e+48], unit="1/cm**3")) and \
      all(em3 > Quantity([3.84e+48], unit="1/cm**3"))

    # test case 4: satellite < 8 and != 6, abundances = photospheric
    temp4, em4 = goes.goes_chianti_tem(longflux, shortflux, satellite=5,
                                       date=date,
                                       abundances="photospheric")
    assert all(temp4 < Quantity([10.42], unit="MK")) and \
      all(temp4 > Quantity([10.41], unit="MK"))
    assert all(em4 < Quantity(8.81e+48, unit="1/cm**3")) and \
      all(em4 > Quantity(8.80e+48, unit="1/cm**3"))

    # test case 5: satellite = 6, date < 1983-06-28, abundances = coronal
    temp5, em5 = goes.goes_chianti_tem(longflux, shortflux, satellite=6,
                                       date="1983-06-27",
                                       abundances="coronal")
    assert all(temp5 < Quantity(12.30, unit="MK")) and \
      all(temp5 > Quantity(12.29, unit="MK"))
    assert all(em5 < Quantity(3.13e+48, unit="1/cm**3")) and \
      all(em5 > Quantity(3.12e+48, unit="1/cm**3"))

    # test case 6: satellite = 6, date < 1983-06-28, abundances = photospheric
    temp6, em6 = goes.goes_chianti_tem(longflux, shortflux, satellite=6,
                                       date="1983-06-27",
                                       abundances="photospheric")
    assert all(temp6 < Quantity(11.44, unit="MK")) and \
      all(temp6 > Quantity(11.43, unit="MK"))
    assert all(em6 < Quantity(6.74e+48, unit="1/cm**3")) and \
      all(em6 > Quantity(6.73e+48, unit="1/cm**3"))

    # test case 7: satellite = 6, date > 1983-06-28, abundances = coronal
    temp7, em7 = goes.goes_chianti_tem(longflux, shortflux, satellite=6,
                                       date=date,
                                       abundances="coronal")
    assert all(temp7 < Quantity(11.34, unit="MK")) and \
      all(temp7 > Quantity(11.33, unit="MK"))
    assert all(em7 < Quantity(4.08e+48, unit="1/cm**3")) and \
      all(em7 > Quantity(4.07e+48, unit="1/cm**3"))

    # test case 8: satellite = 6, date > 1983-06-28, abundances = photospheric
    temp8, em8 = goes.goes_chianti_tem(longflux, shortflux, satellite=6,
                                       date=date,
                                       abundances="photospheric")
    assert all(temp8 < Quantity(10.36, unit="MK")) and \
      all(temp8 > Quantity(10.35, unit="MK"))
    assert all(em8 < Quantity(9.39e+48, unit="1/cm**3")) and \
      all(em8 > Quantity(9.38e+48, unit="1/cm**3"))

def test_radiative_loss_rate():
    # Define input variables.
    goeslc_input = lc.GOESLightCurve.create("2014-01-01 00:00:00",
                                            "2014-01-01 00:00:10")
    not_goeslc = []
    goeslc_no_em = goes.temp_em(goeslc_input)
    del goeslc_no_em.data["em"]
    
    # Check correct exceptions are raised to incorrect inputs
    with pytest.raises(TypeError):
        goes_test = goes.radiative_loss_rate(not_goeslc)

    # Check function gives correct results.
    # Test case 1: GOESLightCurve object with only flux data
    goeslc_test = goes.radiative_loss_rate(goeslc_input)
    goeslc_expected = goes.temp_em(goeslc_input)
    goeslc_expected.data["rad_loss_rate"] = \
      np.array([5.44914366e+19, 5.44914366e+19, 5.43465905e+19,
                5.38282295e+19, 5.42019309e+19])
    assert_frame_equal(goeslc_test.data, goeslc_expected.data)

    # Test case 2: GOESLightCurve object with flux and temperature
    # data, but no EM data.
    goes_test = goes.radiative_loss_rate(goeslc_no_em)
    assert_frame_equal(goeslc_test.data, goeslc_expected.data)

def test_calc_rad_loss_errors():
    # Define input variables
    temp = Quantity([11.0, 11.0, 11.0, 11.0, 11.0, 11.0], unit="MK")
    em = Quantity([4.0e+48, 4.0e+48, 4.0e+48, 4.0e+48, 4.0e+48, 4.0e+48],
                  unit="1/cm**3")
    obstime = np.array([datetime(2014, 1, 1, 0, 0, 0),
                        datetime(2014, 1, 1, 0, 0, 2),
                        datetime(2014, 1, 1, 0, 0, 4),
                        datetime(2014, 1, 1, 0, 0, 6),
                        datetime(2014, 1, 1, 0, 0, 8),
                        datetime(2014, 1, 1, 0, 0, 10)], dtype=object)
    temp_toolong = Quantity(np.append(temp, 0), unit="MK")
    obstime_toolong =  np.array([datetime(2014, 1, 1, 0, 0, 0),
                        datetime(2014, 1, 1, 0, 0, 2),
                        datetime(2014, 1, 1, 0, 0, 4),
                        datetime(2014, 1, 1, 0, 0, 6),
                        datetime(2014, 1, 1, 0, 0, 8),
                        datetime(2014, 1, 1, 0, 0, 10),
                        datetime(2014, 1, 1, 0, 0, 12)], dtype=object))
    obstime_nonchrono = copy.deepcopy(obstime)
    obstime_nonchrono[1] = obstime[-1]
    temp_outofrange = Quantity([101, 11.0, 11.0, 11.0, 11.0, 11.0], unit="MK")
    # Ensure correct exceptions are raised.
    with pytest.raises(ValueError):
        rad_loss_test = goes.calc_rad_loss(temp_toolong, em, obstime)
    with pytest.raises(ValueError):
        rad_loss_test = goes.calc_rad_loss(temp_outofrange, em, obstime)
    with pytest.raises(IOError):
        rad_loss_test = goes.calc_rad_loss(temp, em, obstime_toolong)
    with pytest.raises(ValueError):
        rad_loss_test = goes.calc_rad_loss(temp, em, obstime_nonchrono)
    with pytest.raises(IOError):
        rad_loss_test = goes.calc_rad_loss(temp, em, cumulative=True)

def test_calc_rad_loss():
    # Define input variables
    temp = np.array[11.0, 11.0, 11.0, 11.0, 11.0, 11.0])
    em = np.array([4.0e+48, 4.0e+48, 4.0e+48, 4.0e+48, 4.0e+48, 4.0e+48])
    obstime = np.array([datetime(2014, 1, 1, 0, 0, 0),
                        datetime(2014, 1, 1, 0, 0, 2),
                        datetime(2014, 1, 1, 0, 0, 4),
                        datetime(2014, 1, 1, 0, 0, 6),
                        datetime(2014, 1, 1, 0, 0, 8),
                        datetime(2014, 1, 1, 0, 0, 10)], dtype=object)
    # Test case 1: No kwargs set
    rad_loss_test = goes.calc_rad_loss(temp[:2], em[:2])
    rad_loss_expected = {"rad_loss_rate": np.array([3.01851392e+26,
                                                    3.01851392e+26])}
    assert sorted(rad_loss_test.keys()) == sorted(rad_loss_expected.keys())
    assert np.allclose(rad_loss_test["rad_loss_rate"],
                       rad_loss_expected["rad_loss_rate"], rtol=0.01)

    # Test case 2: obstime kwarg set
    rad_loss_test = goes.calc_rad_loss(temp, em, obstime)
    rad_loss_expected = {
        "rad_loss_rate": np.array([3.01851392e+26, 3.01851392e+26,
                                   3.01851392e+26, 3.01851392e+26,
                                   3.01851392e+26, 3.01851392e+26]),
        "rad_loss_int": 3.01851392e+27,
        "dt": np.array([1, 2, 2, 2, 2, 1], dtype="float64")
        }
    assert sorted(rad_loss_test.keys()) == sorted(rad_loss_expected.keys())
    assert np.allclose(rad_loss_test["rad_loss_rate"],
                       rad_loss_expected["rad_loss_rate"],
                       rtol=0.01)
    assert np.allclose(rad_loss_test["rad_loss_int"],
                       rad_loss_expected["rad_loss_int"], rtol=0.01)
    assert np.allclose(rad_loss_test["dt"], rad_loss_expected["dt"],
                       rtol=0.0001)

    # Test case 3: obstime and cumulative kwargs set
    rad_loss_test = goes.calc_rad_loss(temp, em, obstime, cumulative=True)
    rad_loss_expected = {
        "rad_loss_rate": np.array([3.01851392e+26, 3.01851392e+26,
                                   3.01851392e+26, 3.01851392e+26,
                                   3.01851392e+26, 3.01851392e+26]),
        "rad_loss_int": 3.01851392e+27,
        "rad_loss_cumul": np.array([3.01851392e+26, 9.05554175e+26,
                                    1.50925696e+27, 2.11295974e+27,
                                    2.71666252e+27, 3.01851392e+27]),
        "dt": np.array([1, 2, 2, 2, 2, 1], dtype="float64")
        }
    assert sorted(rad_loss_test.keys()) == sorted(rad_loss_expected.keys())
    assert np.allclose(rad_loss_test["rad_loss_rate"],
                       rad_loss_expected["rad_loss_rate"], rtol=0.0001)
    assert np.allclose(rad_loss_test["rad_loss_int"],
                       rad_loss_expected["rad_loss_int"], rtol=0.0001)
    assert np.allclose(rad_loss_test["rad_loss_cumul"],
                       rad_loss_expected["rad_loss_cumul"], rtol=0.0001)
    assert np.allclose(rad_loss_test["dt"], rad_loss_expected["dt"],
                       rtol=0.0001)

def test_xray_luminosity():
    # Check correct exceptions are raised to incorrect inputs
    not_goeslc = []
    with pytest.raises(TypeError):
        goes_test = goes.xray_luminosity(not_goeslc)
    # Check function gives correct results.
    goeslc_input = lc.GOESLightCurve.create("2014-01-01 00:00:00",
                                            "2014-01-01 00:00:10")
    goeslc_test = goes.xray_luminosity(goeslc_input)
    goeslc_expected = copy.deepcopy(goeslc_input)
    goeslc_expected.data["luminosity_xrsa"] = \
      np.array([2.49831950e+23, 2.49831950e+23, 2.49831950e+23,
                2.52864004e+23, 2.49831950e+23])
    goeslc_expected.data["luminosity_xrsb"] = \
      np.array([9.54399250e+24, 9.54399250e+24, 9.52985195e+24,
                9.52985195e+24, 9.51571139e+24])
    assert_frame_equal(goeslc_test.data, goeslc_expected.data)

def test_goes_lx():
    # Define input values of flux and time.
    longflux = np.array([7e-6, 7e-6, 7e-6, 7e-6, 7e-6, 7e-6])
    shortflux = np.array([7e-7, 7e-7, 7e-7, 7e-7, 7e-7, 7e-7])
    obstime = np.array(["2014-01-01 00:00:00", "2014-01-01 00:00:02",
                        "2014-01-01 00:00:04", "2014-01-01 00:00:06",
                        "2014-01-01 00:00:08",
                        "2014-01-01 00:00:10"], dtype="datetime64[ms]")
    longflux_toolong = np.append(longflux, 0)
    obstime_nonchrono = copy.deepcopy(obstime)
    obstime_nonchrono[1] = obstime[-1]
    # First ensure correct exceptions are raised.
    with pytest.raises(ValueError):
        lx_test = goes.goes_lx(longflux_toolong, shortflux, obstime)
    with pytest.raises(ValueError):
        lx_test = goes.goes_lx(longflux, shortflux, obstime_nonchrono)
    with pytest.raises(IOError):
        lx_test = goes.goes_lx(longflux, shortflux, cumulative=True)

    # Test case 1: no keywords set
    lx_test = goes.goes_lx(longflux[:2], shortflux[:2])
    lx_expected = {"longlum": np.array([1.96860565e+25, 1.96860565e+25]),
                   "shortlum": np.array([1.96860565e+24, 1.96860565e+24])}
    assert sorted(lx_test.keys()) == sorted(lx_expected.keys())
    assert np.allclose(lx_test["longlum"], lx_expected["longlum"], rtol=0.0001)
    assert np.allclose(lx_test["shortlum"], lx_expected["shortlum"],
                       rtol=0.0001)

    # Test case 2: date keyword set only
    lx_test = goes.goes_lx(longflux[:2], shortflux[:2], date="2014-04-21")
    lx_expected = {"longlum": np.array([1.98649103e+25, 1.98649103e+25]),
                   "shortlum": np.array([1.98649103e+24, 1.98649103e+24])}
    assert sorted(lx_test.keys()) == sorted(lx_expected.keys())
    assert np.allclose(lx_test["longlum"], lx_expected["longlum"], rtol=0.0001)
    assert np.allclose(lx_test["shortlum"], lx_expected["shortlum"],
                       rtol=0.0001)

    # Test case 3: obstime keyword set only
    lx_test = goes.goes_lx(longflux, shortflux, obstime)
    lx_expected = {
        "longlum": np.array([1.96860565e+25, 1.96860565e+25, 1.96860565e+25,
                             1.96860565e+25, 1.96860565e+25, 1.96860565e+25]),
        "shortlum": np.array([1.96860565e+24, 1.96860565e+24, 1.96860565e+24,
                              1.96860565e+24, 1.96860565e+24, 1.96860565e+24]),
        "longlum_int": 1.96860565412e+26,
        "shortlum_int": 1.96860565412e+25,
        "dt": np.array([1, 2, 2, 2, 2, 1], dtype="float64")
        }
    assert sorted(lx_test.keys()) == sorted(lx_expected.keys())
    assert np.allclose(lx_test["longlum"], lx_expected["longlum"], rtol=0.0001)
    assert np.allclose(lx_test["shortlum"], lx_expected["shortlum"],
                       rtol=0.0001)
    assert np.allclose(lx_test["longlum_int"], lx_expected["longlum_int"],
                       rtol=0.0001)
    assert np.allclose(lx_test["shortlum_int"], lx_expected["shortlum_int"],
                       rtol=0.0001)
    assert np.allclose(lx_test["dt"], lx_expected["dt"], rtol=0.0001)

    # Test case 4: obstime and cumulative keywords set
    lx_test = goes.goes_lx(longflux, shortflux, obstime, cumulative=True)
    lx_expected = {
        "longlum": np.array([1.96860565e+25, 1.96860565e+25, 1.96860565e+25,
                             1.96860565e+25, 1.96860565e+25, 1.96860565e+25]),
        "shortlum": np.array([1.96860565e+24, 1.96860565e+24, 1.96860565e+24,
                              1.96860565e+24, 1.96860565e+24, 1.96860565e+24]),
        "longlum_int": 1.96860565412e+26,
        "shortlum_int": 1.96860565412e+25,
        "longlum_cumul": np.array([1.96860565e+25, 5.90581696e+25,
                                   9.84302827e+25, 1.37802396e+26,
                                   1.77174509e+26, 1.96860565e+26]),
        "shortlum_cumul": np.array([1.96860565e+24, 5.90581696e+24,
                                    9.84302827e+24, 1.37802396e+25,
                                    1.77174509e+25, 1.96860565e+25]),
        "dt": np.array([1, 2, 2, 2, 2, 1], dtype="float64")}
    assert sorted(lx_test.keys()) == sorted(lx_expected.keys())
    assert np.allclose(lx_test["longlum"], lx_expected["longlum"], rtol=0.0001)
    assert np.allclose(lx_test["shortlum"], lx_expected["shortlum"],
                       rtol=0.0001)
    assert np.allclose(lx_test["longlum_int"], lx_expected["longlum_int"],
                       rtol=0.0001)
    assert np.allclose(lx_test["shortlum_int"], lx_expected["shortlum_int"],
                       rtol=0.0001)
    assert np.allclose(lx_test["longlum_cumul"], lx_expected["longlum_cumul"],
                       rtol=0.0001)
    assert np.allclose(lx_test["shortlum_cumul"],
                       lx_expected["shortlum_cumul"], rtol=0.0001)
    assert np.allclose(lx_test["dt"], lx_expected["dt"], rtol=0.0001)
