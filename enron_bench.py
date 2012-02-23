"""
How to run:

    # Grab the data & extract
    curl -O http://www.cs.cmu.edu/~enron/enron_mail_20110402.tgz
    tar xzf enron_mail_20110402.tgz

    python enron_bench.py </path/to/enron_mail_20110402/maildir>

"""
from __future__ import print_function
import glob
import os
import shutil
import sys
import time
import microsearch


def index_single_email(ms, email, enron_data_dir):
    email_filepath = os.path.join(enron_data_dir, email)

    with open(email_filepath, 'r') as raw_email:
        body = raw_email.read()
        doc_id = email.replace('/', '.')

        # Index it.
        start_time = time.time()
        ms.index(doc_id, {'text': body})
        time_taken = time.time() - start_time

    return time_taken


def index_emails(ms, all_emails, enron_data_dir):
    per_doc_times = []

    for email in all_emails:
        time_taken = index_single_email(ms, email, enron_data_dir)
        per_doc_times.append(time_taken)

    return per_doc_times


def search_emails(ms):
    queries = [
        'expert',
        'question',
        'tax',
        'audit',
        'tax audit',
        'accounting',
        'sex',
        'enron',
    ]
    per_search_times = []

    for query in queries:
        print("Running query `{}`...".format(query))
        start_time = time.time()
        results = ms.search(query)
        time_taken = time.time() - start_time
        print("Found {} results in {:.03f} seconds.".format(results.get('total_hits', 0), time_taken))
        per_search_times.append(time_taken)

    return per_search_times


def main(enron_data_dir):
    data_dir = '/tmp/enron_index'
    shutil.rmtree(data_dir, ignore_errors=True)
    ms = microsearch.Microsearch(data_dir)

    print("Collecting the emails...")
    globby = os.path.join(enron_data_dir, '*/*/*.')
    all_emails = glob.glob(globby)[:1200]

    print("Starting indexing {0} docs...".format(len(all_emails)))
    start_time = time.time()
    per_doc_times = index_emails(ms, all_emails, enron_data_dir)
    time_to_index = time.time() - start_time

    per_doc_avg = sum(per_doc_times) / len(per_doc_times)

    print("Indexing complete.")
    print("Total time taken: {:.03f} seconds".format(time_to_index))
    print("Avg time per doc: {:.03f} seconds".format(per_doc_avg))

    print("Starting searching...")
    start_time = time.time()
    per_search_times = search_emails(ms)
    time_to_search = time.time() - start_time

    per_search_avg = sum(per_search_times) / len(per_search_times)

    print("Searching complete.")
    print("Total time taken: {:.03f} seconds".format(time_to_search))
    print("Avg time per query: {:.03f} seconds".format(per_search_avg))


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: {0} </path/to/enron_mail_20110402/maildir>".format(__file__))
        sys.exit(1)

    enron_data_dir = sys.argv[1]
    main(enron_data_dir)
