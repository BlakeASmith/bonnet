import argparse
import sys
from typing import List, Dict
from dateutil.parser import parse as parse_date
from .database import BonnetDB

class BonnetCLI:
    def __init__(self):
        self.db = BonnetDB()
    
    def store_topic(self, e_id: str, topic_text: str) -> None:
        """Store a master ENTITY record."""
        try:
            self.db.store_entity(e_id, topic_text, topic_text)
            print(f"Stored topic '{topic_text}' with ID {e_id}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def store_fact(self, e_id: str, fact_text: str) -> None:
        """Store a FACT attribute."""
        try:
            # Parse fact as "subject=detail" format
            if '=' in fact_text:
                subject, detail = fact_text.split('=', 1)
                subject = subject.strip()
                detail = detail.strip()
            else:
                subject = "fact"
                detail = fact_text
            
            self.db.store_attribute(e_id, 'FACT', subject, detail)
            print(f"Stored fact '{subject}={detail}' for entity {e_id}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def store_task(self, e_id: str, task_text: str, date: str) -> None:
        """Store a TASK attribute."""
        try:
            # Validate date format
            parse_date(date)
            
            # Parse task as "subject=detail" format
            if '=' in task_text:
                subject, detail = task_text.split('=', 1)
                subject = subject.strip()
                detail = detail.strip()
            else:
                subject = "task"
                detail = task_text
            
            self.db.store_attribute(e_id, 'TASK', subject, detail, date)
            print(f"Stored task '{subject}={detail}' for entity {e_id} with date {date}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def store_rule(self, e_id: str, rule_text: str) -> None:
        """Store a RULE attribute."""
        try:
            # Parse rule as "subject=detail" format
            if '=' in rule_text:
                subject, detail = rule_text.split('=', 1)
                subject = subject.strip()
                detail = detail.strip()
            else:
                subject = "rule"
                detail = rule_text
            
            self.db.store_attribute(e_id, 'RULE', subject, detail)
            print(f"Stored rule '{subject}={detail}' for entity {e_id}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def store_ref(self, e_id: str, ref_text: str, ref_id: str) -> None:
        """Store a REF attribute."""
        try:
            self.db.store_attribute(e_id, 'REF', ref_text, ref_id)
            print(f"Stored reference '{ref_text}' with ID {ref_id} for entity {e_id}")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def search_disambiguate(self, query: str) -> None:
        """Search and disambiguate entities."""
        try:
            results = self.db.search_entities(query)
            
            if not results:
                print(f"No entities found for query: {query}")
                return
            
            if len(results) == 1:
                # Single result, generate context directly
                e_id = results[0]['e_id']
                self.generate_xml_context(e_id)
            else:
                # Multiple results, prompt for selection
                print(f"Found {len(results)} entities matching '{query}':")
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['e_id']}: {result['subject']}")
                
                while True:
                    try:
                        choice = input("Select entity number (or 'q' to quit): ").strip()
                        if choice.lower() == 'q':
                            return
                        
                        choice_num = int(choice)
                        if 1 <= choice_num <= len(results):
                            e_id = results[choice_num - 1]['e_id']
                            self.generate_xml_context(e_id)
                            break
                        else:
                            print(f"Please enter a number between 1 and {len(results)}")
                    except ValueError:
                        print("Please enter a valid number or 'q' to quit")
                    except KeyboardInterrupt:
                        print("\nExiting...")
                        return
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def generate_xml_context(self, e_id: str) -> None:
        """Generate XML context for an entity."""
        try:
            context = self.db.get_entity_context(e_id)
            
            print(f"<context>")
            print(f"{context['e_id']}:\"{context['entity_name']}\"")
            
            for attr in context['attributes']:
                if attr['type'] == 'FACT':
                    print(f"Fact:{context['e_id']}:{attr['subject']}={attr['detail']}")
                elif attr['type'] == 'TASK':
                    print(f"Task:{context['e_id']}:{attr['subject']}={attr['detail']} (due: {attr['date']})")
                elif attr['type'] == 'RULE':
                    print(f"Rule:{context['e_id']}:{attr['subject']}={attr['detail']}")
                elif attr['type'] == 'REF':
                    print(f"Ref:{context['e_id']}:{attr['subject']} (ID: {attr['detail']})")
            
            print(f"</context>")
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    def run(self, args: List[str]) -> None:
        """Main CLI entry point."""
        parser = argparse.ArgumentParser(prog='bonnet', description='Bonnet - Knowledge Base Management CLI')
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Topic command
        topic_parser = subparsers.add_parser('topic', help='Store a master ENTITY record')
        topic_parser.add_argument('--id', required=True, help='Unique Entity ID')
        topic_parser.add_argument('text', help='Topic text')
        
        # Fact command
        fact_parser = subparsers.add_parser('fact', help='Store a FACT attribute')
        fact_parser.add_argument('--about', required=True, help='Entity ID to link to')
        fact_parser.add_argument('text', help='Fact text (format: subject=detail)')
        
        # Task command
        task_parser = subparsers.add_parser('task', help='Store a TASK attribute')
        task_parser.add_argument('--about', required=True, help='Entity ID to link to')
        task_parser.add_argument('--date', required=True, help='Due date (YYYY-MM-DD)')
        task_parser.add_argument('text', help='Task text (format: subject=detail)')
        
        # Rule command
        rule_parser = subparsers.add_parser('rule', help='Store a RULE attribute')
        rule_parser.add_argument('--about', required=True, help='Entity ID to link to')
        rule_parser.add_argument('text', help='Rule text (format: subject=detail)')
        
        # Ref command
        ref_parser = subparsers.add_parser('ref', help='Store a REF attribute')
        ref_parser.add_argument('--about', required=True, help='Entity ID to link to')
        ref_parser.add_argument('--id', required=True, help='Reference ID')
        ref_parser.add_argument('text', help='Reference text')
        
        # Context command
        context_parser = subparsers.add_parser('context', help='Search and generate context')
        context_parser.add_argument('--about', required=True, help='Search query')
        
        # Parse arguments
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return
        
        # Route to appropriate handler
        if parsed_args.command == 'topic':
            self.store_topic(parsed_args.id, parsed_args.text)
        elif parsed_args.command == 'fact':
            self.store_fact(parsed_args.about, parsed_args.text)
        elif parsed_args.command == 'task':
            self.store_task(parsed_args.about, parsed_args.text, parsed_args.date)
        elif parsed_args.command == 'rule':
            self.store_rule(parsed_args.about, parsed_args.text)
        elif parsed_args.command == 'ref':
            self.store_ref(parsed_args.about, parsed_args.text, parsed_args.id)
        elif parsed_args.command == 'context':
            self.search_disambiguate(parsed_args.about)