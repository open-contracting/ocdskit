"""
    Evaluates OCDS JSON files for:
        Validity
        Data Quality
"""
import os
import sys
import ast
import json

import jsonref
import argparse
import collections
import tabulate_ocds
from ocds_dashboard import create_dashboard
import sqlalchemy.exc
import traceback
import pandas as pd

from glob import glob
from time import strftime
from jsonschema import FormatChecker
from jsonschema.validators import validator_for
from sqlalchemy import create_engine, MetaData


def importBIA(engine):
    """
        Imports Basic-Intermediate-Advanced and Documents: ocds_bia.csv, ocds_documents_bia.csv
    """
    try:
        df = pd.read_csv('ocds_bia.csv')
        df.to_sql('ocds_bia', engine, if_exists='replace', index=False)
        print(strftime('%X'), 'Basic-Intermediate-Advanced: ', '{:,}'.format(df.shape[0]))
        df = pd.read_csv('ocds_documents_bia.csv')
        df.to_sql('ocds_documents_bia', engine, if_exists='replace', index=False)
        print(strftime('%X'), 'Basic-Intermediate-Advanced (Documents): ', '{:,}'.format(df.shape[0]))
    except ValueError:
        print(strftime('%X'), 'Error importing Basic-Intermediate-Advanced')
        return False
    return True


def processBIA(engine, tableName):
    """
        Measures a publishers compliance with the Basic - Intermediate - Advanced fields
    """
    excludePrefix = ['ocds', 'publisher']
    columns = ['tableName', 'fieldName', 'rowCount', 'nullCount', 'fillRate']
    dfBIA = pd.DataFrame(columns=columns)
    # Get list of tables - exclude prefixes listed above
    sqlQuery = "SELECT name FROM sqlite_master WHERE type='table'"
    for p in excludePrefix:
        sqlQuery = sqlQuery + " and name not like '" + p + "%'"

    dfTables = pd.read_sql_query(sqlQuery, engine)

    # Loop through tables
    sqlQuery = "SELECT * FROM "
    for index, row in dfTables.iterrows():
        df = pd.read_sql_query(sqlQuery + row[0], engine)
        if df.shape[0] > 0:
            del df['extras']
            dfCount = df.isnull().sum().to_frame(name='nullCount')
            dfCount["tableName"] = row[0]
            dfCount["fieldName"] = dfCount.index
            dfCount["rowCount"] = df.shape[0]
            dfCount["fillRate"] = (dfCount["rowCount"] - dfCount["nullCount"]) / dfCount["rowCount"]
            dfCount.index = range(0, dfCount.shape[0], 1)
            dfCount = dfCount[columns]
            dfBIA = pd.concat([dfCount, dfBIA], ignore_index=True)
    dfBIA.to_sql(tableName, engine, if_exists='replace', index=False)
    return


def validateFiles(jsonFiles, packageSchema, engine):
    """
        Validates the JSON files using the packageSchema if validateJSON flag is set
        Also get package metadata
    """
    validatorFileName = []
    validatorPathName = []
    validatorFieldName = []
    validatorErrorDescription = []
    metadataFilename = []
    metdataURI = []
    metadataPublishedDate = []
    metadataPublisherScheme = []
    metadataPublisherUid = []
    metadatapublisherName = []
    metadataPublisherUri = []
    metadataLicense = []
    metadataPublicationPolicy = []
    packageMetadataPrefix = ['uri', 'publishedDate', 'publisher', 'license', 'publicationPolicy']
    packageMetadataSubKey = {'publisher': ['scheme', 'name', 'uri', 'uid']}
    packageMetadataDict = {'filename': None, 'uri': None, 'publishedDate': None, 'publisher.scheme': None,
                           'publisher.uid': None, 'publisher.name': None, 'publisher.uri': None, 'license': None,
                           'publicationPolicy': None}

    """try:"""
    v = validator_for(packageSchema)
    validator = v(schema=packageSchema, format_checker=FormatChecker())

    for publisherFile in jsonFiles:
        with open(publisherFile, 'r') as JSONFile:
            JSONData = json.load(JSONFile)
            for error in sorted(validator.iter_errors(JSONData), key=str):
                errorPath = list(collections.deque(error.absolute_path))
                validatorFileName.append(os.path.basename(publisherFile))
                validatorPathName.append('/'.join(str(e) for e in errorPath))
                validatorFieldName.append(str(error.instance))
                validatorErrorDescription.append(error.message)

            packageMetadataDict['filename'] = os.path.basename(publisherFile)
            if isinstance(JSONData, dict) and os.path.getsize(publisherFile) < 1024000:
                for key, value in JSONData.items():
                    if key in packageMetadataPrefix:
                        if key in packageMetadataSubKey.keys():
                            for subKey in packageMetadataSubKey[key]:
                                if subKey in value:
                                    packageMetadataDict[key + '.' + subKey] = value[subKey]
                        else:
                            packageMetadataDict[key] = value
            else:
                print(os.path.basename(publisherFile))
                print(type(JSONData))
                # ToDO: Something that handles large files consistently

            metadataFilename.append(packageMetadataDict['filename'])
            metdataURI.append(packageMetadataDict['uri'])
            metadataPublishedDate.append(packageMetadataDict['publishedDate'])
            metadataPublisherScheme.append(packageMetadataDict['publisher.scheme'])
            metadataPublisherUid.append(packageMetadataDict['publisher.uid'])
            metadatapublisherName.append(packageMetadataDict['publisher.name'])
            metadataPublisherUri.append(packageMetadataDict['publisher.uri'])
            metadataLicense.append(packageMetadataDict['license'])
            metadataPublicationPolicy.append(packageMetadataDict['publicationPolicy'])
            packageMetadataDict = {'filename': None, 'uri': None, 'publishedDate': None,
                                   'publisher.scheme': None, 'publisher.uid': None,
                                   'publisher.name': None, 'publisher.uri': None, 'license': None,
                                   'publicationPolicy': None}

    validatorData = {'fileName': validatorFileName, 'pathName': validatorPathName, 'fieldName': validatorFieldName,
                     'errorDescription': validatorErrorDescription}
    metaData = {'filename': metadataFilename, 'uri': metdataURI, 'publishedDate': metadataPublishedDate,
                'publisher.scheme': metadataPublisherScheme, 'publisher.uid': metadataPublisherUid,
                'publisher.name': metadatapublisherName, 'publisher.uri': metadataPublisherUri,
                'license': metadataLicense, 'publicationPolicy': metadataPublicationPolicy}

    """except:
        print(strftime('%X'), 'Error: Validating JSON')
        return None
    """
    return validatorData, metaData


def getReleaseSchema(localSchema, localPackageSchema):
    """
        Returns the OCDS schema from the open-contracting.org website
    """
    releaseSchema, packageSchema, releaseSchemaURL, releasePackageURL = None, None, None, None

    print(strftime('%X'), 'Loading Schema')
    if os.path.isfile(localSchema):
        print(strftime('%X'), 'Loading Local Schema:', localSchema)
        try:
            with open(localSchema) as data_file:
                releaseSchema = json.load(data_file)
            releaseSchemaURL = 'file://' + os.path.abspath(localSchema)
        except OSError:
            return None, None, None, None
    else:
        releaseSchemaURL = "http://standard.open-contracting.org/1.0/en/" + os.path.basename(localSchema)
        print(strftime('%X'), 'Loading Remote Schema:', releaseSchemaURL)
        try:
            releaseSchema = jsonref.load_uri(releaseSchemaURL)
        except TypeError:
            return None, None, None, None

    print(strftime('%X'), 'Loading Package Schema')
    if os.path.isfile(localPackageSchema):
        print(strftime('%X'), 'Loading Local Package Schema:', localPackageSchema)
        try:
            with open(localPackageSchema) as data_file:
                packageSchema = json.load(data_file)
                releasePackageURL = 'file://' + os.path.abspath(localSchema)
        except OSError:
            return None, None, None, None
    else:
        releasePackageURL = "http://standard.open-contracting.org/1.0/en/" + os.path.basename(localPackageSchema)
        print(strftime('%X'), 'Loading Remote Package Schema:', releasePackageURL)
        try:
            packageSchema = jsonref.load_uri(releasePackageURL)
        except TypeError:
            return None, None, None, None

    if 'id' in releaseSchema:
        versionNumber = releaseSchema['id'].split('/')[4]

    print(strftime('%X'), 'Schema version:', versionNumber)
    return releaseSchema, packageSchema, releaseSchemaURL, releasePackageURL, versionNumber


def checkParams(publisher, database, container, refresh, schema, package, validate, dashboard, country):
    """
        Checks the supplied parameters are valid
    """

    print('Parameters Provided')
    print('-------------------')
    print('Publisher Path: ', publisher)
    print('Database Path:  ', database)
    print('OCDS Container: ', container)
    print('Refresh Metdata:', refresh)
    print('Refresh Schema: ', schema)
    print('Validate JSON:  ', validate)
    print('Generate Dashboard:  ', dashboard)
    print('Country-City:  ', country)

    # Check Params
    if publisher is None or not os.path.isdir(str(publisher)):
        print(strftime('%X'), 'Error: Provide the publisher file path')
        return False

    if database is None:
        print(strftime('%X'), 'Error: Provide the database file path')
        return False

    if container is None or container not in ['R', 'P']:
        print(strftime('%X'), 'Error: Provide the container type as P - Packaged Records or R - Releases')
        return False

    if refresh is None or refresh not in [True, False, 'True', "False"]:
        print(strftime('%X'), 'Error: Provide the refresh metadata flag as True/False')
        return False

    if schema is None or schema not in [True, False, 'True', "False"]:
        if not os.path.isfile(schema):
            print(strftime('%X'), 'Error: Provide the latest schema flag as True/False or a local schema file')
            return False

    if package is None or package not in [True, False, 'True', "False"]:
        if not os.path.isfile(package):
            print(strftime('%X'), 'Error: Provide the latest package flag as True/False or a local package file')
            return False

    if validate is None or validate not in [True, False, 'True', "False"]:
        print(strftime('%X'), 'Error: Provide the validate JSON flag as True/False')
        return False

    if dashboard is None or dashboard not in [True, False, 'True', "False"]:
        print(strftime('%X'), 'Error: Provide the generate dashboard flag as True/False')
        return False
    if country is None:
        print(strftime('%X'), 'Error: Provide the Country or City name')
        return False

    return True


def main():
    os.system('clear')
    print('***************')
    print('OCDS Validation')
    print('***************')
    print('')
    print('Python Version:    ', sys.version)
    print('')

    # Initialise arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('--publisher', help='Publisher File Path')
    parser.add_argument('--database', help='Database File Path')
    parser.add_argument('--container', help='Packaged Records (P) or Releases (R)', default='R')
    parser.add_argument('--refresh', help='Refresh metadata flag', default=True)
    parser.add_argument('--schema', help='Latest schema flag', default=True)  # To do, provide schema reference number
    #  to use. Right now, ignore the schema and use latest
    parser.add_argument('--package', help='Latest package flag', default=True)  # To do, provide schema reference
    # number to use. Right now, ignore the schema and use latest
    parser.add_argument('--validate', help='Validate JSON flag', default=True)
    parser.add_argument('--dashboard', help='Generate dashboard flag', default=False)
    parser.add_argument('--country', help='Country or City name', default="Sample")
    parser.add_argument('--lang', help='Language to generate the dashboard. English (en) or Spanish (es) supported',
                        default='en')
    args = parser.parse_args()

    # Check arguments
    if not checkParams(args.publisher, args.database, args.container, args.refresh, args.schema, args.package,
                       args.validate, args.dashboard, args.country):
        return

    # Initialise other variables
    publisherFilesTableName = 'publisher_files'
    packageMetadataTableName = 'publisher_metadata'
    validationLogTableName = 'publisher_validation'
    jsonFiles = glob(args.publisher + '/*.json')
    resultsBIATableName = 'publisher_BIA'
    releasePackageURL = None
    releaseSchemaURL = None
    packageSchema = None
    releaseSchema = None
    localPackageSchema = None
    localSchema = None
    validateJSON = None
    refresh = None

    if args.container == "P":
        localSchema = args.schema if args.schema not in [True, False, 'True', "False"] else "versioned-release" \
                                                                                            "-validation-schema.json "
        localPackageSchema = args.package if args.package not in [True, False, 'True', "False"] else "record-package" \
                                                                                                     "-schema.json "
    else:
        localSchema = args.schema if args.schema not in [True, False, 'True', "False"] else "release-schema.json"
        localPackageSchema = args.package if args.package not in [True, False, 'True', "False"] \
            else "release-package-schema.json "

    if isinstance(args.refresh, str):
        refresh = ast.literal_eval(args.refresh)
    else:
        refresh = args.refresh

    if isinstance(args.validate, str):
        validateJSON = ast.literal_eval(args.validate)
    else:
        validateJSON = args.validate

    print('Release Schema: ', localSchema)
    print('Package Schema: ', localPackageSchema)
    print('')

    # Get release schema
    releaseSchema, packageSchema, releaseSchemaURL, releasePackageURL, version = getReleaseSchema(localSchema,
                                                                                                  localPackageSchema)
    if releaseSchema is None:
        print(strftime('%X'), 'Error: Could not load release and package schema')
        return

    # Get the database
    print(strftime('%X'), 'Opening database')
    metadata, engine = None, None
    try:
        if refresh:
            metadata, engine = tabulate_ocds.create_db('sqlite:///' + args.database, releaseSchema, drop=refresh)
        else:
            engine = create_engine('sqlite:///' + args.database)
            metadata = MetaData(engine)
    except ValueError:
        traceback.print_exc()
        e = sys.exc_info()[0]
        print(strftime('%X'), 'Error: Could not open database:', e)

    if metadata is None or engine is None:
        return
    fileNumber = 0
    if refresh:
        # Tabulate files
        print(strftime('%X'), 'Tabulate Files')
        try:
            tabulate_ocds.upload_files(metadata, engine, releaseSchema, jsonFiles, False)  # To do: extended container
            #  for (V)ersioned released
        except sqlalchemy.exc.StatementError as e:
            print(strftime('%X'), e)

        # Add list of files
        df = pd.DataFrame({'filename': jsonFiles}, columns=['filename'])
        df.to_sql(publisherFilesTableName, engine, if_exists='replace', index=False)
        fileNumber = df.shape[0]
        print(strftime('%X'), 'Loaded publishers files:', '{:,}'.format(df.shape[0]))

    meta = None
    if validateJSON:
        validationData, metaData = validateFiles(jsonFiles, packageSchema, engine)
        if validationData is not None:
            df = pd.DataFrame(validationData, columns=['fileName', 'pathName', 'fieldName', 'errorDescription'])
            df.to_sql(validationLogTableName, engine, if_exists='replace', index=False)

            print(strftime('%X'), 'Loaded validation errors:', '{:,}'.format(df.shape[0]))
        if metaData is not None:
            df = pd.DataFrame(metaData)
            df.to_sql(packageMetadataTableName, engine, if_exists='replace', index=False)
            meta = df
            print(strftime('%X'), 'Loaded package metadata:', '{:,}'.format(df.shape[0]))

    # Import Basic-Intermediate-Advanced
    if not importBIA(engine):
        return

    # Process Basic-Intermediate-Advanced
    processBIA(engine, resultsBIATableName)

    print('')
    if args.dashboard:
        create_dashboard(args.country, engine, meta, fileNumber, version, args.lang)

    print(strftime('%X'), 'Complete')


if __name__ == "__main__":
    main()
