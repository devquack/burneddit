import sys
import praw
import yaml
import time
from loguru import logger

def main():

    config_file_path = 'config.yaml'
    example_file_path = 'config.yaml.example'

    logger.info(f'Loading config file {config_file_path}')
    try: config_file = open(config_file_path)
    except:
        logger.error(f'Error: Unable to open config file {config_file_path}')
        sys.exit(1)

    logger.info(f'Parsing config file {config_file_path}')
    try: config = yaml.load(config_file, Loader=yaml.FullLoader)
    except Exception as e:
        logger.error(f'Error: Unable to parse config file {config_file_path}')
        for line in str(e).splitlines(): logger.error(line)
        sys.exit(1)

    logger.info(f'Loading example file {example_file_path}')
    try: example_file = open(example_file_path)
    except:
        logger.error(f'Error: Unable to open example file {example_file_path}')
        sys.exit(1)

    logger.info(f'Parsing example file {example_file_path}')
    try: example = yaml.load(example_file, Loader=yaml.FullLoader)
    except Exception as e:
        logger.error(f'Error: Unable to parse example file {example_file_path}')
        for line in str(e).splitlines(): logger.error(line)
        sys.exit(1)
    
    missing = get_missing_dict_keys(example, config)
    if len(missing) > 0:
        for item in missing: logger.error(f'Error: Missing config file key {item}')
        sys.exit(1)

    for user in config['users']:
        
        logger.info('')
        logger.info(f'Loading reddit connection for {user["username"]}')
        try:
            reddit = praw.Reddit(
                username=user['username'],
                password=user['password'],
                client_id=user['client_id'],
                client_secret=user['client_secret'],
                user_agent='burneddit')
            reddit.validate_on_submit = True
            submissions = list(reddit.redditor(user['username']).submissions.new(limit=None))
            comments = list(reddit.redditor(user['username']).comments.new(limit=None))
        except:
            logger.error(f'Error: Unable to load reddit connection for {user["username"]}')
            continue

        logger.info('')
        logger.info(f'--- Submissions for {user["username"]} ---')
        logger.info(f'Number of submissions: {len(submissions)}')
        if len(submissions) > 0:
            burn(config['submissions']['burn_type'], 
                config['submissions']['max_age_days'], 
                config['submissions']['template'], 
                submissions)
        logger.info('---')
        logger.info('')
        logger.info(f'--- Comments for {user["username"]} ---')
        
        logger.info(f'Number of comments: {len(comments)}')
        if len(comments) > 0:
            burn(config['comments']['burn_type'], 
                config['comments']['max_age_days'], 
                config['comments']['template'], 
                comments)
        logger.info('---')

def burn(burn_type, max_age_days, template, items):
    logger.info(f'Burn type: {burn_type}')
    logger.info(f'Max age: {max_age_days} days')
    logger.info(f'Template: {template}')
    if burn_type not in ['delete', 'overwrite']:
        logger.error(f'Error: Unable to determine burn type \'{burn_type}\'')
        return False
    for item in items:
        item_age = (time.time() - item.created_utc) / 86400
        if item_age < max_age_days:
            status = 'Skipped'
        elif burn_type == 'delete':
            status = 'Deleted'
            item.delete()
        elif burn_type == 'overwrite':
            status = 'Overwritten'
            item.edit(template)
        logger.info(f'# Handling Item - ID: {item.id}, Age: {round(item_age, 2)} days, Status: {status}')

def get_missing_dict_keys(source, check):
    def _get_keys(d, prepend=''):
      keys = []
      for k, v in d.items():
        if isinstance(v, dict):
          keys.extend(_get_keys(v, '{}/{}'.format(prepend, k)))
        else: keys.append('{}/{}'.format(prepend, k))
      return keys
    source_keys = _get_keys(source)
    check_keys = _get_keys(check)
    return [k for k in source_keys if k not in check_keys]

if __name__ == '__main__': main()