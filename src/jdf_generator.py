"""
JDF (Job Definition Format) file generator for EPSON PP-100 robot
"""

import logging
import os
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from xml.dom import minidom

from config import Config


class JDFGenerator:
    """Generator for JDF files for EPSON PP-100 disc burning robot."""

    def __init__(self, config: Config):
        """Initialize JDF generator.

        Args:
            config: Application configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # JDF namespaces
        self.namespaces = {
            "jdf": "http://www.CIP4.org/JDFSchema_1_1",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }

    def create_burn_job_jdf(
        self,
        iso_path: str,
        job_id: str = None,
        burn_speed: str = None,
        verify: bool = None,
        copies: int = 1,
    ) -> str:
        """Create a JDF file for disc burning job.

        Args:
            iso_path: Path to the ISO file to burn
            job_id: Unique job identifier (generated if None)
            burn_speed: Burn speed (e.g., '8x', '16x')
            verify: Whether to verify after burning
            copies: Number of copies to burn

        Returns:
            Path to generated JDF file
        """
        if job_id is None:
            job_id = str(uuid.uuid4())

        if burn_speed is None:
            burn_speed = self.config.burn_speed

        if verify is None:
            verify = self.config.verify_after_burn

        # Ensure JDF folder exists
        self.config.ensure_folders_exist()

        # Create JDF filename
        iso_filename = Path(iso_path).stem
        jdf_filename = f"{job_id}_{iso_filename}.jdf"
        jdf_path = self.config.jdf_folder / jdf_filename

        try:
            # Create JDF XML structure
            jdf_root = self._create_jdf_root(job_id)

            # Add job description
            job_desc = ET.SubElement(jdf_root, "Description")
            job_desc.set("Name", f"Disc Burn Job - {iso_filename}")
            job_desc.set("DescriptiveName", f"Burning {copies} copie(s) of {iso_filename}")

            # Add audit information
            self._add_audit_info(jdf_root)

            # Add resource pool
            resource_pool = ET.SubElement(jdf_root, "ResourcePool")

            # Add component resource (the disc)
            component_resource = self._create_component_resource(resource_pool)

            # Add digital asset resource (the ISO file)
            digital_asset = self._create_digital_asset_resource(resource_pool, iso_path)

            # Add burning parameters
            burning_params = self._create_burning_parameters(
                resource_pool, burn_speed, verify, copies
            )

            # Add process
            process = self._create_burning_process(
                jdf_root, component_resource, digital_asset, burning_params
            )

            # Write JDF file with pretty formatting
            self._write_jdf_file(jdf_root, jdf_path)

            self.logger.info(f"Generated JDF file: {jdf_path}")
            return str(jdf_path)

        except Exception as e:
            self.logger.error(f"Error creating JDF file: {e}")
            raise

    def _create_jdf_root(self, job_id: str) -> ET.Element:
        """Create the root JDF element.

        Args:
            job_id: Unique job identifier

        Returns:
            JDF root element
        """
        jdf_root = ET.Element("JDF")
        jdf_root.set("xmlns:jdf", self.namespaces["jdf"])
        jdf_root.set("xmlns:xsi", self.namespaces["xsi"])
        jdf_root.set("ID", job_id)
        jdf_root.set("Type", "Product")
        jdf_root.set("Version", "1.3")
        jdf_root.set("Status", "Waiting")

        return jdf_root

    def _add_audit_info(self, jdf_root: ET.Element):
        """Add audit information to JDF.

        Args:
            jdf_root: JDF root element
        """
        # Created audit
        created_audit = ET.SubElement(jdf_root, "AuditPool")
        created = ET.SubElement(created_audit, "Created")
        created.set("AgentName", "EPSON_Burner_App")
        created.set("AgentVersion", "1.0")
        created.set("TimeStamp", datetime.now().isoformat())

    def _create_component_resource(self, resource_pool: ET.Element) -> ET.Element:
        """Create component resource for the disc.

        Args:
            resource_pool: Resource pool element

        Returns:
            Component resource element
        """
        component = ET.SubElement(resource_pool, "Component")
        component.set("ID", "Component_1")
        component.set("Class", "Consumable")
        component.set("Status", "Available")

        # Component details
        component_type = ET.SubElement(component, "ComponentType")
        component_type.text = "Disc"

        return component

    def _create_digital_asset_resource(
        self, resource_pool: ET.Element, iso_path: str
    ) -> ET.Element:
        """Create digital asset resource for the ISO file.

        Args:
            resource_pool: Resource pool element
            iso_path: Path to ISO file

        Returns:
            Digital asset resource element
        """
        digital_asset = ET.SubElement(resource_pool, "DigitalPrintingParams")
        digital_asset.set("ID", "DigitalAsset_1")
        digital_asset.set("Class", "Parameter")
        digital_asset.set("Status", "Available")

        # ISO file information
        file_spec = ET.SubElement(digital_asset, "FileSpec")
        file_spec.set("URL", f"file://{iso_path}")

        # Get file size
        file_size = os.path.getsize(iso_path)
        file_size_elem = ET.SubElement(file_spec, "FileSize")
        file_size_elem.text = str(file_size)

        return digital_asset

    def _create_burning_parameters(
        self, resource_pool: ET.Element, burn_speed: str, verify: bool, copies: int
    ) -> ET.Element:
        """Create burning parameters resource.

        Args:
            resource_pool: Resource pool element
            burn_speed: Burn speed setting
            verify: Whether to verify after burning
            copies: Number of copies

        Returns:
            Burning parameters resource element
        """
        burning_params = ET.SubElement(resource_pool, "BurningParams")
        burning_params.set("ID", "BurningParams_1")
        burning_params.set("Class", "Parameter")
        burning_params.set("Status", "Available")

        # Burn speed
        speed_elem = ET.SubElement(burning_params, "BurnSpeed")
        speed_elem.text = burn_speed

        # Verification
        verify_elem = ET.SubElement(burning_params, "Verification")
        verify_elem.text = "true" if verify else "false"

        # Number of copies
        copies_elem = ET.SubElement(burning_params, "Copies")
        copies_elem.text = str(copies)

        return burning_params

    def _create_burning_process(
        self,
        jdf_root: ET.Element,
        component: ET.Element,
        digital_asset: ET.Element,
        burning_params: ET.Element,
    ) -> ET.Element:
        """Create the burning process element.

        Args:
            jdf_root: JDF root element
            component: Component resource
            digital_asset: Digital asset resource
            burning_params: Burning parameters resource

        Returns:
            Process element
        """
        process = ET.SubElement(jdf_root, "Process")
        process.set("ID", "Process_1")
        process.set("Types", "Burning")

        # Input resources
        input_resources = ET.SubElement(process, "Input")

        # Component input
        component_input = ET.SubElement(input_resources, "ResourceReference")
        component_input.set("rRef", component.get("ID"))

        # Digital asset input
        digital_input = ET.SubElement(input_resources, "ResourceReference")
        digital_input.set("rRef", digital_asset.get("ID"))

        # Parameters
        params = ET.SubElement(process, "Parameter")
        params_ref = ET.SubElement(params, "ResourceReference")
        params_ref.set("rRef", burning_params.get("ID"))

        return process

    def _write_jdf_file(self, jdf_root: ET.Element, jdf_path: Path):
        """Write JDF XML to file with pretty formatting.

        Args:
            jdf_root: JDF root element
            jdf_path: Path to write JDF file
        """
        # Convert to string with proper encoding
        rough_string = ET.tostring(jdf_root, encoding="utf-8")
        reparsed = minidom.parseString(rough_string)

        # Pretty print with 2-space indentation
        pretty_xml = reparsed.toprettyxml(indent="  ", encoding=None)

        # Remove empty lines
        lines = [line for line in pretty_xml.split("\n") if line.strip()]
        clean_xml = "\n".join(lines)

        # Write to file
        with open(jdf_path, "w", encoding="utf-8") as f:
            f.write(clean_xml)

    def create_template_jdf(self, template_path: str = None) -> str:
        """Create a template JDF file for testing.

        Args:
            template_path: Path to save template (uses default if None)

        Returns:
            Path to created template file
        """
        if template_path is None:
            template_path = self.config.jdf_folder / "template.jdf"

        # Create a basic template JDF
        jdf_root = self._create_jdf_root("TEMPLATE_JOB")

        # Add basic structure
        job_desc = ET.SubElement(jdf_root, "Description")
        job_desc.set("Name", "Template JDF for EPSON PP-100")

        self._add_audit_info(jdf_root)

        # Write template
        self._write_jdf_file(jdf_root, Path(template_path))

        self.logger.info(f"Created template JDF: {template_path}")
        return template_path

    def validate_jdf_file(self, jdf_path: str) -> bool:
        """Validate a JDF file.

        Args:
            jdf_path: Path to JDF file

        Returns:
            True if valid, False otherwise
        """
        try:
            # Try to parse the XML
            tree = ET.parse(jdf_path)
            root = tree.getroot()

            # Check for required elements
            if root.tag != "JDF":
                self.logger.error("Root element is not JDF")
                return False

            # Check for required attributes
            required_attrs = ["ID", "Type", "Version", "Status"]
            for attr in required_attrs:
                if attr not in root.attrib:
                    self.logger.error(f"Missing required attribute: {attr}")
                    return False

            self.logger.info(f"JDF file is valid: {jdf_path}")
            return True

        except ET.ParseError as e:
            self.logger.error(f"JDF file parsing error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error validating JDF file: {e}")
            return False

    def get_jdf_info(self, jdf_path: str) -> dict:
        """Extract information from a JDF file.

        Args:
            jdf_path: Path to JDF file

        Returns:
            Dictionary with JDF information
        """
        try:
            tree = ET.parse(jdf_path)
            root = tree.getroot()

            info = {
                "id": root.get("ID"),
                "type": root.get("Type"),
                "version": root.get("Version"),
                "status": root.get("Status"),
                "description": "",
                "components": [],
                "processes": [],
            }

            # Extract description if available
            for desc in root.findall("Description"):
                if "Name" in desc.attrib:
                    info["description"] = desc.get("Name")
                break

            # Extract component information
            for component in root.findall(".//Component"):
                component_info = {
                    "id": component.get("ID"),
                    "type": component.findtext("ComponentType", ""),
                    "status": component.get("Status", ""),
                }
                info["components"].append(component_info)

            # Extract process information
            for process in root.findall("Process"):
                process_info = {"id": process.get("ID"), "types": process.get("Types", "")}
                info["processes"].append(process_info)

            return info

        except Exception as e:
            self.logger.error(f"Error reading JDF info: {e}")
            return {}
