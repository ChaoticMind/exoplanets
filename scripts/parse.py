#!/usr/bin/env python
import requests
import argparse
import json
import datetime
from collections import namedtuple, OrderedDict
from calendar import timegm

# all planets
CSV_URL = "https://www.astro.keele.ac.uk/jkt/tepcat/allplanets-csv.csv"
ASCII_URL = "https://www.astro.keele.ac.uk/jkt/tepcat/allplanets-ascii.txt"
# individual planets
HUMAN_URL = "https://www.astro.keele.ac.uk/jkt/tepcat/planets/{}.html"
# references
ARXIV_URL = "https://arxiv.org/abs/{}"
FALLBACK_URL = "http://adsabs.harvard.edu/abs/{}"
# other urls
HELP_URL = "https://www.astro.keele.ac.uk/jkt/tepcat/html-quantities.html"


def fetch_source(web, URI=None):
    if web:
        try:
            r = requests.get(URI)
        except requests.exceptions.SSLError:
            print("warning: couldn't verify TLS certificate. "
                  "Using plain http as fallback...")
            r = requests.get(URI.replace('https', 'http'))
        if r.status_code != 200:
            raise RuntimeError("Received http code: {}".format(r.status_code))
        else:
            source = r.text
    else:
        with open(URI) as f:
            source = f.read()
    return source.split('\n')


def parse_csv(src, skip_err_margins):
    new_src = [x.replace(',', ' ') for x in src[1:]]
    return parse_ascii(new_src, skip_err_margins)


def parse_ascii(src, skip_err_margins):
    props = [
        'system',
        # stellar properties
        'Teff', 'Teff_erru', 'Teff_errd', 'FeH', 'FeH_erru', 'FeH_errd',
        'Msun', 'Msun_erru', 'Msun_errd', 'Rsun', 'Rsun_erru', 'Rsun_errd',
        'cgs', 'cgs_erru', 'cgs_errd', 'rhosun', 'rhosun_erru', 'rhosun_errd',
        # system properties?
        'Porb',
        'ecc', 'ecc_erru', 'ecc_errd', 'a_AU', 'a_AU_erru', 'a_AU_errd',
        # planetary properties
        'Mjup', 'Mjup_erru', 'Mjup_errd', 'Rjup', 'Rjup_erru', 'Rjup_errd',
        'ms2', 'ms2_erru', 'ms2_errd', 'rhoJup', 'rhoJup_erru', 'rhoJup_errd',
        'Teqk', 'Teqk_erru', 'Teqk_errd',
        # references
        'd_ref', 'r_ref']
    Properties = namedtuple('Properties', props)

    ret = []
    if skip_err_margins:
        def get_data(param):
            return float(getattr(x, param))
    else:
        def get_data(param):
            ret = OrderedDict()
            ret['value'] = float(getattr(x, param))
            ret['error_plus'] = float(
                getattr(x, '{}_{}'.format(param, 'erru')))
            ret['error_minus'] = float(
                getattr(x, '{}_{}'.format(param, 'errd')))
            return ret

    for line in src:
        if line.startswith('#') or not line:
            # print('Skipping commented line: {}'.format(line))
            continue
        x = Properties(*line.split())
        row = OrderedDict()
        row['system'] = x.system
        row['period'] = float(x.Porb)
        row['eccentricity'] = get_data('ecc')
        row['semimajor_AU'] = get_data('a_AU')

        row['stellar_properties'] = OrderedDict()
        row['stellar_properties']['temp_k'] = get_data('Teff')
        # # alternatively, could also just inline the values/errors like so:
        # row['stellar_properties']['temp_k_value'] = x.Teff
        # row['stellar_properties']['temp_k_error_plus'] = x.Teff_erru
        # row['stellar_properties']['temp_k_error_minus'] = x.Teff_errd
        row['stellar_properties']['metal_log'] = get_data('FeH')
        row['stellar_properties']['mass_sol'] = get_data('Msun')
        row['stellar_properties']['radius_sol'] = get_data('Rsun')
        row['stellar_properties']['gravity_log_cgs'] = get_data('cgs')
        row['stellar_properties']['density_sol'] = get_data('rhosun')

        row['planetary_properties'] = OrderedDict()
        row['planetary_properties']['mass_jup'] = get_data('Mjup')
        row['planetary_properties']['radius_jup'] = get_data('Rjup')
        row['planetary_properties']['gravity'] = get_data('ms2')
        row['planetary_properties']['density_jup'] = get_data('rhoJup')
        row['planetary_properties']['temp_eq_k'] = get_data('Teqk')

        row['references'] = OrderedDict()
        row['references']['human_url'] = HUMAN_URL.format(x.system)
        if x.d_ref.startswith('arXiv'):
            row['references']['discovery'] = ARXIV_URL.format(x.d_ref)
        else:
            row['references']['discovery'] = FALLBACK_URL.format(
                x.d_ref).replace('+', '&')

        if x.r_ref.startswith('arXiv'):
            row['references']['recent'] = ARXIV_URL.format(x.r_ref)
        else:
            row['references']['recent'] = FALLBACK_URL.format(
                x.r_ref).replace('+', '&')
        ret.append(row)
    return ret


def build_output(data, timestamp):
    ret = OrderedDict()
    if timestamp:
        now = datetime.datetime.utcnow()
        ret['fetched_data_human_utc'] = '{0:%Y-%b-%d %X}'.format(now)
        ret['fetched_data_unix_utc'] = timegm(now.timetuple())
    else:
        ret['fetched_date_human'] = "unknown"
        ret['fetched_date_unix'] = 0
    # ret['units_info'] = HELP_URL
    ret['units_info'] = HELP_URL
    ret['data'] = data
    return ret


def main():
    parser = argparse.ArgumentParser(
        description="convert source exoplanet (transit) data into json")
    parser.add_argument("-f", "--from-file",
                        help="fetch source from file (instead of web)",
                        type=str)
    parser.add_argument("-t", "--type",
                        help="source type (csv or ascii)",
                        type=str, choices=["ascii", "csv"], default="ascii")
    parser.add_argument("-s", "--skip-errors", action="store_true",
                        help="If specified, skips error margins (+/-)"
                             "for each data point")
    parser.add_argument("-e", "--export", help="export output to file")
    parser.add_argument("-q", "--quiet", help="don't print output to stdout",
                        action="store_true")
    args = parser.parse_args()

    if args.type == "ascii":
        if args.from_file is None:
            source = fetch_source(web=True, URI=ASCII_URL)
        else:
            source = fetch_source(web=False, URI=args.from_file)
        data = parse_ascii(source, args.skip_errors)
    elif args.type == "csv":
        if args.from_file is None:
            source = fetch_source(web=True, URI=CSV_URL)
        else:
            source = fetch_source(web=False, URI=args.from_file)
        data = parse_csv(source, args.skip_errors)

    out = build_output(data, timestamp=True if not args.from_file else False)
    formatted = json.dumps(out, indent=4)
    if not args.quiet:
        print(formatted)
    if args.export:
        with open(args.export, 'w') as f:
            f.write(formatted)
        print('written to file: {}'.format(args.export))

if __name__ == '__main__':
    main()
