import click
import subprocess
import sys
from pathlib import Path
from typing import List

@click.group()
def cli():
    """SQLProxy Test Runner"""
    pass

@cli.command()
@click.option('--category', '-c', multiple=True, 
              help='Test kategorisi (unit/integration/performance/security)')
@click.option('--parallel/--no-parallel', default=True,
              help='Parallel test execution')
@click.option('--workers', '-w', default=4,
              help='Parallel worker sayısı')
def run(category: List[str], parallel: bool, workers: int):
    """Testleri çalıştırır"""
    cmd = ['pytest']
    
    if category:
        markers = [f"-m {cat}" for cat in category]
        cmd.extend(markers)
        
    if parallel:
        cmd.extend(['-n', str(workers)])
        
    cmd.extend(['--cov=sqlproxy', '--cov-report=xml'])
    
    result = subprocess.run(cmd)
    sys.exit(result.returncode)

@cli.command()
def doc():
    """Test dokümantasyonu oluşturur"""
    from tests.doc_generator import TestDocGenerator
    generator = TestDocGenerator()
    generator.generate_test_docs()
    click.echo("Test documentation generated!")

if __name__ == '__main__':
    cli()